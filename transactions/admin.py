from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vendor_name', 'amount', 'transaction_type', 'date']
    list_filter = ['transaction_type', 'flag', 'category', 'date']
    search_fields = ['user__email', 'vendor_name', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Receipt', {
            'fields': ('user', 'receipt')
        }),
        ('Transaction Details', {
            'fields': ('vendor_name', 'amount', 'date', 'category')
        }),
        ('Classification', {
            'fields': ('transaction_type', 'flag')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
