from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
import cloudinary.uploader
from .models import Receipt
from .forms import ReceiptUploadForm


@login_required
def upload_receipt(request):
    """
    Receipt upload view.
    - Gets file from user
    - Uploads to Cloudinary
    - Creates Receipt record
     """
    if request.method == 'POST':
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
                    original_filename=uploaded_file.name,
                    status='pending'  # Waiting for OCR
                )
                
                messages.success(
                    request, 
                    'Receipt uploaded successfully! OCR processing started...'
                )
                
                # OCR function will be added in PHASE 3.3
                # Redirect to receipt list page
                return redirect('receipt_list')
                
            except Exception as e:
                messages.error(
                    request,
                    f'Error during upload: {str(e)}'
                )
    else:
        form = ReceiptUploadForm()
    
    return render(request, 'receipts/upload.html', {
        'form': form,
        'page_title': 'Fatura Yükle'
    })


@login_required
def receipt_list(request):
    """
    List of user's uploaded receipts.
    """
    receipts = Receipt.objects.filter(user=request.user)
    
    return render(request, 'receipts/receipt_list.html', {
        'receipts': receipts,
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

