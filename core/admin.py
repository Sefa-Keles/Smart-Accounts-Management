from django.contrib import admin
from .models import Category, Subscription

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_system', 'user', 'created_at']
    list_filter = ['is_system', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end']
    list_filter = ['plan', 'status', 'created_at']
    search_fields = ['user__email', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at', 'stripe_subscription_id']
