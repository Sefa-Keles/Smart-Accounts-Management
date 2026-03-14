from django.db import models
from django.contrib.auth.models import User
from core.models import Category
from receipts.models import Receipt

class Transaction(models.Model):
    """
    Income/Expense Transactions
    """
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    FLAG_CHOICES = [
        ('business', 'Business'),
        ('personal', 'Personal'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    
    # Receipt connection (optional - manual entry also possible)
    receipt = models.ForeignKey(Receipt, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Transaction Details
    vendor_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    
    # Classification
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    flag = models.CharField(max_length=50, choices=FLAG_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.vendor_name} - {self.amount} ({self.transaction_type})"
