from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    """
    Expense/Income categories
    Examples: Travel, Food, Office Supplies, etc.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    is_system = models.BooleanField(default=True)  # System-provided categories
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    User Subscription Plan
    """
    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_end = models.DateTimeField()
    stripe_subscription_id = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"
