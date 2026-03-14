from datetime import datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Category, Subscription
from transactions.models import Transaction


def home(request):
    """Public landing page."""
    return render(request, 'core/home.html')


@login_required(login_url='login')
def dashboard(request):
    """User dashboard with current-month financial summary."""
    today = timezone.now().date()
    session_filters = request.session.get('transaction_filters', {})

    clear_filters = request.GET.get('clear_filters') == '1'
    request_has_filter_params = any(
        key in request.GET for key in ['month', 'start_date', 'end_date']
    )

    if clear_filters:
        request.session.pop('transaction_filters', None)
        selected_month = today.strftime('%Y-%m')
        start_date = ''
        end_date = ''
    elif request_has_filter_params:
        selected_month = request.GET.get('month', '').strip()
        start_date = request.GET.get('start_date', '').strip()
        end_date = request.GET.get('end_date', '').strip()
        request.session['transaction_filters'] = {
            'month': selected_month,
            'start_date': start_date,
            'end_date': end_date,
        }
    else:
        selected_month = session_filters.get('month', today.strftime('%Y-%m'))
        start_date = session_filters.get('start_date', '')
        end_date = session_filters.get('end_date', '')

    month_transactions = Transaction.objects.filter(user=request.user)
    filter_label = 'Current month'

    if start_date and end_date:
        try:
            start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            month_transactions = month_transactions.filter(date__range=[start_obj, end_obj])
            filter_label = f'{start_obj:%d %b %Y} - {end_obj:%d %b %Y}'
        except ValueError:
            selected_month = today.strftime('%Y-%m')
            start_date = ''
            end_date = ''

    if not start_date or not end_date:
        if selected_month:
            try:
                year, month = selected_month.split('-')
                month_transactions = month_transactions.filter(
                    date__year=int(year),
                    date__month=int(month),
                )
                filter_label = datetime(int(year), int(month), 1).strftime('%B %Y')
            except (ValueError, TypeError):
                month_transactions = month_transactions.filter(
                    date__year=today.year,
                    date__month=today.month,
                )
                selected_month = today.strftime('%Y-%m')
        else:
            month_transactions = month_transactions.filter(
                date__year=today.year,
                date__month=today.month,
            )
            selected_month = today.strftime('%Y-%m')

    totals = month_transactions.values('transaction_type').annotate(total=Sum('amount'))
    income = Decimal('0.00')
    expense = Decimal('0.00')

    for row in totals:
        if row['transaction_type'] == 'income':
            income = row['total'] or Decimal('0.00')
        elif row['transaction_type'] == 'expense':
            expense = row['total'] or Decimal('0.00')

    expense_by_category = (
        month_transactions.filter(transaction_type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    category_labels = []
    category_totals = []
    for item in expense_by_category:
        category_name = item['category__name'] or 'Uncategorized'
        category_labels.append(category_name)
        category_totals.append(float(item['total'] or 0))

    context = {
        'income_total': income,
        'expense_total': expense,
        'net_balance': income - expense,
        'recent_transactions': month_transactions.order_by('-date', '-created_at')[:5],
        'expense_category_labels': category_labels,
        'expense_category_totals': category_totals,
        'selected_month': selected_month,
        'start_date': start_date,
        'end_date': end_date,
        'filter_label': filter_label,
    }
    return render(request, 'core/dashboard.html', context)


@login_required(login_url='login')
def category_list(request):
    """List categories and allow creating a custom category."""
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()

        if not category_name:
            messages.error(request, 'Category name cannot be empty.')
            return redirect('category_list')

        existing_category = Category.objects.filter(name__iexact=category_name).first()
        if existing_category:
            messages.warning(request, 'This category already exists.')
            return redirect('category_list')

        Category.objects.create(
            name=category_name,
            is_system=False,
            user=request.user,
        )
        messages.success(request, 'Category created successfully.')
        return redirect('category_list')

    system_categories = Category.objects.filter(is_system=True).order_by('name')
    custom_categories = Category.objects.filter(user=request.user, is_system=False).order_by('name')

    return render(
        request,
        'core/categories.html',
        {
            'system_categories': system_categories,
            'custom_categories': custom_categories,
            'page_title': 'Categories',
        },
    )


@login_required(login_url='login')
def category_delete(request, category_id):
    """Delete one of the current user's custom categories."""
    category = get_object_or_404(
        Category,
        id=category_id,
        user=request.user,
        is_system=False,
    )

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')

    return redirect('category_list')


@login_required(login_url='login')
def subscription_plans(request):
    """Display available subscription plans."""
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()

    return render(
        request,
        'core/subscription_plans.html',
        {
            'active_subscription': active_subscription,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'page_title': 'Subscription Plans',
        },
    )


@login_required(login_url='login')
@require_POST
def create_checkout_session(request):
    """Create a Stripe checkout session for a selected plan."""
    selected_plan = request.POST.get('plan', '').strip().lower()
    if selected_plan not in ['basic', 'premium']:
        return HttpResponseBadRequest('Invalid plan selected.')

    if not settings.STRIPE_SECRET_KEY:
        return HttpResponseBadRequest('Stripe secret key is not configured.')

    plan_price_map = {
        'basic': settings.STRIPE_PRICE_BASIC,
        'premium': settings.STRIPE_PRICE_PREMIUM,
    }
    price_id = plan_price_map.get(selected_plan)
    if not price_id:
        return HttpResponseBadRequest('Stripe price id is not configured for the selected plan.')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        mode='subscription',
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        customer_email=request.user.email,
        metadata={
            'user_id': str(request.user.id),
            'plan': selected_plan,
        },
        success_url=f"{settings.SITE_URL}{reverse('subscription_success')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.SITE_URL}{reverse('subscription_cancel')}",
    )

    return JsonResponse({'checkout_url': checkout_session.url})


@login_required(login_url='login')
def subscription_success(request):
    """Handle successful Stripe checkout redirection."""
    messages.success(request, 'Subscription checkout completed successfully.')
    return redirect('subscription_plans')


@login_required(login_url='login')
def subscription_cancel(request):
    """Handle cancelled Stripe checkout redirection."""
    messages.info(request, 'Subscription checkout was cancelled.')
    return redirect('subscription_plans')
