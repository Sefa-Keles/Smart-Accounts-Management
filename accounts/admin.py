from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_date_joined', 'user_is_active']
    list_filter = ['user__is_active', 'user__date_joined']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

    @admin.display(ordering='user__date_joined', description='Date Joined')
    def user_date_joined(self, obj):
        return obj.user.date_joined

    @admin.display(ordering='user__is_active', description='Is Active')
    def user_is_active(self, obj):
        return obj.user.is_active
