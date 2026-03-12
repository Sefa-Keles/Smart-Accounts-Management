from django import forms
from django.db.models import Q

from core.models import Category

from .models import Transaction


class TransactionForm(forms.ModelForm):
    """Form used for editing an existing transaction."""

    # Override date field to render a browser date-picker with Bootstrap styling
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"],
    )

    class Meta:
        model = Transaction
        # Exclude user, receipt, and timestamps — only expose editable fields
        fields = [
            "vendor_name",
            "amount",
            "date",
            "transaction_type",
            "flag",
            "category",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit category choices to the current user's categories and system defaults
        if user is None:
            self.fields["category"].queryset = Category.objects.none()
        else:
            self.fields["category"].queryset = Category.objects.filter(
                Q(user=user) | Q(is_system=True)
            ).distinct()