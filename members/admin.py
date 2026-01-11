# members/admin.py
from django.contrib import admin, messages
from django.db.models import Q
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import MemberProfile, MembershipPlan


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "membership_level",
        "is_member",
        "is_active_member_display",
        "membership_started",
        "membership_expires",
        "auto_renew",
        "next_billing_date",
    )
    list_filter = ("membership_level", "is_member", "auto_renew")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("membership_started", "membership_expires")

    @admin.display(boolean=True, description="Active now?")
    def is_active_member_display(self, obj):
        return obj.is_active_member


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    """Admin interface for managing membership plans"""
    list_display = ('name', 'slug', 'price_display', 'is_active', 'active_members_count', 'display_order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'description')
    list_editable = ('is_active', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'slug', 'price', 'is_active', 'display_order'),
            'description': 'To remove a plan from the website, set "Is active" to False. Plans with active member subscriptions cannot be deleted.'
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
                    messages.success(request, f"The Membership Plan \"{obj.name}\" has been successfully inactivated.")
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
    
    # Note: We allow delete permission so the delete button shows
    # The actual deletion prevention happens in get_deleted_objects and delete_model/delete_queryset
    
    # Note: We don't override get_deleted_objects to add items to protected list
    # Instead, we let deletion proceed to delete_model/delete_queryset where we intercept
    # and show a friendly message
    
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
        messages.success(request, f"Successfully deleted {count} membership plan(s).")
