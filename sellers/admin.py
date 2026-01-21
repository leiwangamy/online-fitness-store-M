from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Seller, SellerMembershipPlan

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


@admin.register(SellerMembershipPlan)
class SellerMembershipPlanAdmin(admin.ModelAdmin):
    """Admin interface for managing seller membership plans"""
    list_display = ('name', 'slug', 'seller_display', 'price_display', 'is_active', 'is_approved', 'active_members_count', 'display_order', 'created_at')
    list_filter = ('is_active', 'is_approved', 'seller', 'created_at')
    search_fields = ('name', 'slug', 'description', 'seller__display_name', 'seller__user__email')
    list_editable = ('is_active', 'is_approved', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('seller', 'name', 'slug', 'price', 'is_active', 'is_approved', 'display_order'),
            'description': 'To remove a plan from the website, set "Is active" to False. Plans with active member subscriptions cannot be deleted. "Is approved" controls whether the plan appears publicly and in navigation.'
        }),
        ('Description', {
            'fields': ('description', 'details')
        }),
        ('Member Information', {
            'fields': ('active_members_info',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'active_members_info')
    
    @admin.display(description="Seller")
    def seller_display(self, obj):
        """Display the seller who owns this plan"""
        seller_name = obj.seller.display_name or obj.seller.user.username
        return format_html('<strong>{}</strong>', seller_name)
    
    def save_model(self, request, obj, form, change):
        """Override save to show success message when inactivating a plan"""
        if change:  # Only for existing objects (not new ones)
            # Get the original object from database
            try:
                original = self.model.objects.get(pk=obj.pk)
                # Check if is_active changed from True to False (inactivation)
                if original.is_active and not obj.is_active:
                    # Plan is being inactivated
                    super().save_model(request, obj, form, change)
                    messages.success(request, f"The Seller Membership Plan \"{obj.name}\" has been successfully inactivated.")
                    return
            except self.model.DoesNotExist:
                pass
        
        # Normal save (new object or no inactivation)
        super().save_model(request, obj, form, change)
    
    def active_members_count(self, obj):
        """Display count of active members for this plan"""
        if obj.pk:
            count = obj.get_active_member_count()
            if count > 0:
                return format_html('<strong style="color: red;">{} active member(s)</strong>', count)
            return "0 active members"
        return "-"
    active_members_count.short_description = "Active Members"
    
    def active_members_info(self, obj):
        """Display information about active members for this plan"""
        if not obj.pk:
            return "Save the plan first to see member information."
        
        count = obj.get_active_member_count()
        if count > 0:
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">'
                '<strong>Warning:</strong> This plan has <strong>{}</strong> active member subscription(s).<br>'
                'Active membership exists. Please inactivate instead of deleting.<br>'
                'To remove this plan from the website, set "Is active" to False.<br>'
                'The plan cannot be deleted until all member subscriptions expire.'
                '</div>',
                count
            )
        return format_html(
            '<div style="padding: 10px; background: #d4edda; border: 1px solid #28a745; border-radius: 4px;">'
            'This plan has no active member subscriptions. It can be safely deleted if needed.'
            '</div>'
        )
    active_members_info.short_description = "Member Status"
    
    def delete_model(self, request, obj):
        """Override delete to block deletion for plans with active members"""
        if obj.has_active_members():
            # Store object info for use in response_delete
            active_count = obj.get_active_member_count()
            messages.error(
                request,
                f"Cannot delete '{obj.name}' - Active membership exists ({active_count} active subscription(s)). Please inactivate instead."
            )
            # Don't call super().delete_model() - this prevents deletion
            # response_delete will detect object still exists and redirect
            return
        
        # No active members - proceed with deletion
        super().delete_model(request, obj)
    
    def response_delete(self, request, obj_display, obj_id):
        """Override delete response to handle blocked deletions"""
        # Check if deletion was blocked (if object still exists, deletion was prevented)
        try:
            obj = self.model.objects.get(pk=obj_id)
            # Object still exists - deletion was blocked in delete_model
            # Error message already shown in delete_model, just redirect
            opts = self.model._meta
            return HttpResponseRedirect(reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist'))
        except self.model.DoesNotExist:
            # Object was deleted successfully - proceed with normal response (shows success message)
            return super().response_delete(request, obj_display, obj_id)
    
    def delete_queryset(self, request, queryset):
        """Override bulk delete to block deletion and show warnings for plans with active members"""
        plans_with_members = []
        
        # Check all plans first
        for obj in queryset:
            if obj.has_active_members():
                active_count = obj.get_active_member_count()
                plans_with_members.append(f"{obj.name} ({active_count} active subscription(s))")
        
        # If ANY plan has active members, block ALL deletions and only show error message
        if plans_with_members:
            plans_list = ", ".join(plans_with_members)
            messages.error(
                request,
                f"Cannot delete the following plan(s) - Active membership exists: {plans_list}. Please inactivate instead."
            )
            # Don't delete ANY plans if any have active members (no success message)
            # Return without calling super() to prevent Django's default success message
            return
        
        # Only delete if NO plans have active members
        # Call parent delete_queryset which will show success message
        count = queryset.count()
        queryset.delete()
        # Show our own success message to ensure consistency
        messages.success(request, f"Successfully deleted {count} seller membership plan(s).")
