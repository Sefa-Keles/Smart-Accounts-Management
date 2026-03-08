from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'uploaded_at', 'ocr_vendor']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['user__email', 'original_filename', 'ocr_vendor']
    readonly_fields = ['uploaded_at', 'cloudinary_url', 'id', 'ocr_raw_text']
    
    fieldsets = (
        ('User & File Info', {
            'fields': ('user', 'original_filename', 'cloudinary_url', 'uploaded_at')
        }),
        ('OCR Data', {
            'fields': ('ocr_vendor', 'ocr_date', 'ocr_amount', 'ocr_raw_text'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
