from django import forms
from django.db.models import Q
from core.models import Category


class ReceiptUploadForm(forms.Form):
    """
    Receipt upload form.
    - Accepts only image and PDF files
    - Maximum 5MB file size limit
    """
    
    file = forms.FileField(
        label='Receipt File',
        help_text='JPG, PNG, or PDF format, maximum 5MB',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/jpg,application/pdf',
        })
    )
    
    def clean_file(self):
        """
        File validation:
        - File type check (JPG, PNG, PDF)
        - Size check (max 5MB)
        """
        file = self.cleaned_data.get('file')
        
        if file:
            # File extension validation
            allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
            file_extension = file.name.split('.')[-1].lower()
            
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    'Only JPG, PNG, or PDF files are accepted.'
                )
            
            # File size validation (5MB = 5 * 1024 * 1024 bytes)
            max_size = 5 * 1024 * 1024
            if file.size > max_size:
                raise forms.ValidationError(
                    f'File size is too large. Maximum {max_size / (1024 * 1024):.0f}MB allowed.'
                )
        
        return file


class ReceiptReviewForm(forms.Form):
    """
    Review form used before creating a transaction from a receipt.
    OCR values are used as initial values, but user can edit everything.
    """

    vendor_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"],
    )
    transaction_type = forms.ChoiceField(
        choices=[("expense", "Expense"), ("income", "Income")],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    flag = forms.ChoiceField(
        choices=[("personal", "Personal"), ("business", "Business")],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is None:
            self.fields["category"].queryset = Category.objects.none()
        else:
            self.fields["category"].queryset = Category.objects.filter(
                Q(user=user) | Q(is_system=True)
            ).distinct()
