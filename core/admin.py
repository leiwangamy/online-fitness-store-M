from django.contrib import admin
from .models import CompanyInfo, UserDeletion


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    """Admin interface for editing company contact information"""
    
    list_display = ['phone', 'email', 'updated_at']
    fieldsets = (
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Location & Description', {
            'fields': ('address', 'description')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


@admin.register(UserDeletion)
class UserDeletionAdmin(admin.ModelAdmin):
    """Admin interface for viewing deleted user accounts"""
    
    list_display = ['user', 'user_email', 'deleted_at', 'days_remaining', 'can_recover']
    list_filter = ['deleted_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'deleted_at', 'days_until_permanent', 'can_recover']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'deleted_at', 'reason')
        }),
        ('Deletion Status', {
            'fields': ('days_until_permanent', 'can_recover'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def days_remaining(self, obj):
        days = obj.days_until_permanent
        if days == 0:
            return "Permanent"
        return f"{days} days"
    days_remaining.short_description = "Days Remaining"
    
    def has_add_permission(self, request):
        return False  # Deletions are created through the deletion process
