from django import forms
from .models import Receipt


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
