from django.conf import settings
from django.utils import timezone

from core.models import Subscription
from receipts.models import Receipt
from transactions.models import Transaction


def get_user_plan(user):
    """Return the effective plan key for a user."""
    subscription = Subscription.objects.filter(user=user, status='active').first()
    if subscription and subscription.plan in settings.PLAN_LIMITS:
        return subscription.plan
    return 'basic'


def get_plan_limit(plan, limit_key):
    """Return numeric limit or None (unlimited)."""
    return settings.PLAN_LIMITS.get(plan, settings.PLAN_LIMITS['basic']).get(limit_key)


def _month_bounds(reference=None):
    ref = reference or timezone.now().date()
    return ref.year, ref.month


def get_monthly_usage(user):
    """Return current month usage for receipts and transactions."""
    year, month = _month_bounds()
    return {
        'receipts': Receipt.objects.filter(user=user, uploaded_at__year=year, uploaded_at__month=month).count(),
        'transactions': Transaction.objects.filter(user=user, created_at__year=year, created_at__month=month).count(),
    }


def can_create_receipt(user):
    """Check whether user can upload another receipt this month."""
    plan = get_user_plan(user)
    limit_value = get_plan_limit(plan, 'max_receipts_per_month')
    if limit_value is None:
        return True, plan, None

    usage = get_monthly_usage(user)['receipts']
    return usage < limit_value, plan, limit_value


def can_create_transaction(user):
    """Check whether user can create another transaction this month."""
    plan = get_user_plan(user)
    limit_value = get_plan_limit(plan, 'max_transactions_per_month')
    if limit_value is None:
        return True, plan, None

    usage = get_monthly_usage(user)['transactions']
    return usage < limit_value, plan, limit_value
