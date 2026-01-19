from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import Seller

User = get_user_model()


class SellerAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'display_name', 'email_verified', 'status', 'commission_rate', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username', 'display_name', 'business_name')
    readonly_fields = ('created_at', 'updated_at', 'user_email_display', 'email_verified_display', 'user_date_joined')
    
    fieldsets = (
        ('User Account Information', {
            'fields': ('user', 'user_email_display', 'email_verified_display', 'user_date_joined'),
            'description': 'User account details - email, verification status, and account creation date.'
        }),
        ('Seller Profile', {
            'fields': ('display_name',)
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_description'),
            'classes': ('collapse',)
        }),
        ('Seller Status', {
            'fields': ('status',),
            'description': 'Change status to APPROVED to allow seller to add products.'
        }),
               ('Commission', {
                   'fields': ('commission_rate',),
                   'description': 'Commission rate as a decimal (e.g., 0.10 = 10%)'
               }),
               ('Payout Settings', {
                   'fields': ('payout_hold_days',),
                   'description': 'Number of days to hold earnings before they become available for payout (default: 7 days). Can be changed manually per seller.'
               }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email in list view"""
        return obj.user.email if obj.user.email else obj.user.username
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_email_display(self, obj):
        """Display user email in detail view"""
        if obj.user.email:
            return format_html('<strong>{}</strong>', obj.user.email)
        return obj.user.username
    user_email_display.short_description = 'User Email'
    
    def email_verified(self, obj):
        """Display email verification status in list view"""
        try:
            from allauth.account.models import EmailAddress
            email_address = EmailAddress.objects.get(user=obj.user, email=obj.user.email)
            if email_address.verified:
                return format_html('<span style="color: green;">✓ Verified</span>')
            else:
                return format_html('<span style="color: red;">✗ Not Verified</span>')
        except Exception:
            return format_html('<span style="color: orange;">?</span>')
    email_verified.short_description = 'Email Verified'
    
    def email_verified_display(self, obj):
        """Display email verification status in detail view"""
        try:
            from allauth.account.models import EmailAddress
            email_address = EmailAddress.objects.get(user=obj.user, email=obj.user.email)
            if email_address.verified:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Email Verified</span><br>'
                    '<small>Verified on: {}</small>',
                    email_address.verified_at.strftime('%Y-%m-%d %H:%M:%S') if email_address.verified_at else 'N/A'
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">✗ Email Not Verified</span><br>'
                    '<small>User must verify their email address before they can fully use their account.</small>'
                )
        except Exception as e:
            return format_html('<span style="color: orange;">⚠ Unable to check verification status</span>')
    email_verified_display.short_description = 'Email Verification Status'
    
    def user_date_joined(self, obj):
        """Display when user account was created"""
        return obj.user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if obj.user.date_joined else 'N/A'
    user_date_joined.short_description = 'Account Created'
    
    actions = ['approve_sellers', 'reject_sellers']
    
    def approve_sellers(self, request, queryset):
        """Admin action to approve selected sellers"""
        updated = queryset.update(status=Seller.STATUS_APPROVED)
        self.message_user(request, f'{updated} seller(s) approved successfully.')
    approve_sellers.short_description = "Approve selected sellers"
    
    def reject_sellers(self, request, queryset):
        """Admin action to reject selected sellers"""
        updated = queryset.update(status=Seller.STATUS_REJECTED)
        self.message_user(request, f'{updated} seller(s) rejected.')
    reject_sellers.short_description = "Reject selected sellers"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter the user dropdown when adding sellers manually in admin.
        Exclude users who already have a seller profile.
        Note: Users can also apply through the public application form.
        """
        if db_field.name == 'user':
            # Get the current object being edited (if any)
            obj = kwargs.get('obj') or getattr(request, '_current_seller_obj', None)
            
            if obj and obj.pk:
                # Editing existing seller: include current user, exclude others with sellers
                existing_seller_user_ids = Seller.objects.exclude(pk=obj.pk).values_list('user_id', flat=True)
                queryset = User.objects.exclude(id__in=existing_seller_user_ids).order_by('email')
            else:
                # Adding new seller: exclude all users who already have a seller
                existing_seller_user_ids = Seller.objects.values_list('user_id', flat=True)
                queryset = User.objects.exclude(id__in=existing_seller_user_ids).order_by('email')
            
            kwargs['queryset'] = queryset
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """Store the current object for use in formfield_for_foreignkey"""
        request._current_seller_obj = obj
        return super().get_form(request, obj, **kwargs)
    
    def has_change_permission(self, request, obj=None):
        """
        Only staff can approve sellers.
        This is already enforced by Django admin (only staff can access admin),
        but we make it explicit here.
        """
        return request.user.is_staff
    
    def has_add_permission(self, request):
        """Only staff can add sellers."""
        return request.user.is_staff


# Explicitly register Seller model (more reliable than decorator)
admin.site.register(Seller, SellerAdmin)
