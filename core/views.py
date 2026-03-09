from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from transactions.models import Transaction


def home(request):
    """Public landing page."""
    return render(request, 'core/home.html')


@login_required(login_url='login')
def dashboard(request):
    """User dashboard with current-month financial summary."""
    today = timezone.now().date()
    month_transactions = Transaction.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month,
    )

    totals = month_transactions.values('transaction_type').annotate(total=Sum('amount'))
    income = Decimal('0.00')
    expense = Decimal('0.00')

    for row in totals:
        if row['transaction_type'] == 'income':
            income = row['total'] or Decimal('0.00')
        elif row['transaction_type'] == 'expense':
            expense = row['total'] or Decimal('0.00')

    context = {
        'income_total': income,
        'expense_total': expense,
        'net_balance': income - expense,
        'recent_transactions': Transaction.objects.filter(user=request.user)[:5],
    }
    return render(request, 'core/dashboard.html', context)
