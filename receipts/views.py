from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
import cloudinary.uploader
from urllib.parse import urlparse
from core.plan_limits import can_create_receipt
from core.plan_limits import can_create_transaction
from transactions.models import Transaction
from .models import Receipt
from .forms import ReceiptUploadForm, ReceiptReviewForm
from .utils import process_receipt_with_ocr


def _public_id_from_url(file_url):
    """Fallback public_id parser for receipts created before public_id storage."""
    try:
        path = urlparse(file_url).path
        marker = '/upload/'
        if marker not in path:
            return None

        public_part = path.split(marker, 1)[1]

        # Strip version segment such as v1712345678/
        if public_part.startswith('v') and '/' in public_part:
            version_part, rest = public_part.split('/', 1)
            if version_part[1:].isdigit():
                public_part = rest

        # Strip extension
        if '.' in public_part:
            public_part = public_part.rsplit('.', 1)[0]

        return public_part
    except Exception:
        return None


@login_required
def upload_receipt(request):
    """
    Receipt upload view.
    - Gets file from user
    - Uploads to Cloudinary
    - Creates Receipt record
    - Processes OCR data via OCR.space
    """
    if request.method == 'POST':
        allowed, plan, limit_value = can_create_receipt(request.user)
        if not allowed:
            messages.error(
                request,
                f"{plan.title()} plan monthly receipt limit reached ({limit_value}). Upgrade your subscription to continue.",
            )
            return redirect('subscription_plans')

        form = ReceiptUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Get file from form
                uploaded_file = form.cleaned_data['file']
                
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    uploaded_file,
                    folder='receipts',  # Save to receipts folder in Cloudinary
                    resource_type='auto',  # Auto type detection (image/pdf)
                )
                
                # Create Receipt record
                receipt = Receipt.objects.create(
                    user=request.user,
                    cloudinary_url=upload_result['secure_url'],
                    cloudinary_public_id=upload_result.get('public_id'),
                    original_filename=uploaded_file.name,
                    status='pending'  # Waiting for OCR
                )

                # Process OCR after successful upload
                ocr_result = process_receipt_with_ocr(receipt.cloudinary_url)
                if ocr_result.get('success'):
                    receipt.ocr_raw_text = ocr_result.get('raw_text')
                    receipt.ocr_vendor = ocr_result.get('vendor')
                    receipt.ocr_amount = ocr_result.get('amount')
                    receipt.ocr_date = ocr_result.get('date')
                    receipt.status = 'reviewed'
                    receipt.save(
                        update_fields=['ocr_raw_text', 'ocr_vendor', 'ocr_amount', 'ocr_date', 'status']
                    )
                    messages.success(
                        request,
                        'Receipt uploaded and OCR processed successfully.'
                    )
                else:
                    messages.warning(
                        request,
                        f"Receipt uploaded, but OCR could not be completed: {ocr_result.get('error')}. Please enter data manually."
                    )
                
                # Always continue with the review step before saving transaction
                return redirect('receipt_review', receipt_id=receipt.id)
                
            except Exception as e:
                messages.error(
                    request,
                    f'Error during upload: {str(e)}'
                )
    else:
        form = ReceiptUploadForm()
    
    return render(request, 'receipts/upload.html', {
        'form': form,
        'page_title': 'Upload Receipt'
    })


@login_required
def receipt_list(request):
    """
    List of user's uploaded receipts.
    """
    receipts = Receipt.objects.filter(user=request.user)
    paginator = Paginator(receipts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'receipts/receipt_list.html', {
        'receipts': page_obj,
        'page_obj': page_obj,
        'page_title': 'My Receipts'
    })


@login_required
def receipt_detail(request, receipt_id):
    """
    Receipt details and OCR results.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)
    
    return render(request, 'receipts/receipt_detail.html', {
        'receipt': receipt,
        'page_title': f'Receipt #{receipt.id}'
    })


@login_required
def receipt_review(request, receipt_id):
    """
    Review OCR result (or manual input) and create transaction only on confirmation.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)

    initial_data = {
        'vendor_name': receipt.ocr_vendor or '',
        'description': '',
        'amount': receipt.ocr_amount,
        'date': receipt.ocr_date,
        'transaction_type': 'expense',
        'flag': 'personal',
    }

    if request.method == 'POST':
        form = ReceiptReviewForm(request.POST, user=request.user)
        if form.is_valid():
            allowed, plan, limit_value = can_create_transaction(request.user)
            if not allowed:
                messages.error(
                    request,
                    f"{plan.title()} plan monthly transaction limit reached ({limit_value}). Upgrade your subscription to continue.",
                )
                return redirect('subscription_plans')

            Transaction.objects.create(
                user=request.user,
                receipt=receipt,
                vendor_name=form.cleaned_data['vendor_name'],
                description=form.cleaned_data['description'],
                amount=form.cleaned_data['amount'],
                date=form.cleaned_data['date'],
                transaction_type=form.cleaned_data['transaction_type'],
                flag=form.cleaned_data['flag'],
                category=form.cleaned_data['category'],
            )

            receipt.ocr_vendor = form.cleaned_data['vendor_name']
            receipt.ocr_amount = form.cleaned_data['amount']
            receipt.ocr_date = form.cleaned_data['date']
            receipt.status = 'saved'
            receipt.save(update_fields=['ocr_vendor', 'ocr_amount', 'ocr_date', 'status'])

            messages.success(request, 'Transaction saved successfully.')
            return redirect('receipt_detail', receipt_id=receipt.id)
    else:
        form = ReceiptReviewForm(initial=initial_data, user=request.user)

    return render(request, 'receipts/review.html', {
        'receipt': receipt,
        'form': form,
        'page_title': f'Review Receipt #{receipt.id}',
    })


@login_required
def receipt_delete(request, receipt_id):
    """Delete a user's receipt after confirmation, including related data."""
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)

    if request.method == 'POST':
        # Delete related transaction(s) linked with this receipt
        Transaction.objects.filter(receipt=receipt, user=request.user).delete()

        # Remove file from Cloudinary
        public_id = receipt.cloudinary_public_id or _public_id_from_url(receipt.cloudinary_url)
        if public_id:
            cloudinary.uploader.destroy(public_id, resource_type='image', invalidate=True)
            cloudinary.uploader.destroy(public_id, resource_type='raw', invalidate=True)

        receipt.delete()
        messages.success(request, 'Receipt and related transaction deleted successfully.')
        return redirect('receipt_list')

    return render(request, 'receipts/delete.html', {'receipt': receipt})

