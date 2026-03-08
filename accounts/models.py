from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    User Profile - Extends Django's built-in User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    class Meta:
        ordering = ['-user__date_joined']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.user.first_name} {self.user.last_name}"
