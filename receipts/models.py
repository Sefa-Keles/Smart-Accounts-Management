from django.db import models
from django.contrib.auth.models import User

class Receipt(models.Model):
    """
    Receipt/Invoice - Stored on Cloudinary
    """
    STATUS_CHOICES = [
        ('pending', 'Pending OCR'),
        ('reviewed', 'OCR Reviewed'),
        ('saved', 'Transaction Saved'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    
    # File stored on Cloudinary
    cloudinary_url = models.CharField(max_length=500)  # URL returned from Cloudinary
    cloudinary_public_id = models.CharField(max_length=255, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    
    # Data extracted by OCR
    ocr_vendor = models.CharField(max_length=255, null=True, blank=True)
    ocr_date = models.DateField(null=True, blank=True)
    ocr_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ocr_raw_text = models.TextField(null=True, blank=True)  # Raw OCR output
    
    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Receipt {self.id} - {self.user.email} ({self.status})"
