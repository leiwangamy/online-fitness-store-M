from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import CompanySettings


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Company Branding", {
            "fields": ("company_name", "logo", "favicon", "tagline"),
            "description": "Customize your company's name, logo, and tagline. These appear in the header and throughout the site."
        }),
        ("Contact Information", {
            "fields": ("support_email", "phone_number", "address"),
            "description": "Contact details that appear in the footer and contact pages."
        }),
        ("Order Settings", {
            "fields": ("pickup_only", "shipping_policy"),
            "description": "Control checkout and fulfillment options. When 'Pickup Only' is enabled, customers can only select pickup at the first available location. Shipping address and shipping fees will be disabled. Shipping policy text will be hidden when pickup_only is enabled."
        }),
        ("Hero Section", {
            "fields": ("hero_title", "hero_subtitle", "hero_cta_text", "hero_cta_url", "hero_image"),
            "description": "Customize the homepage hero section. The hero section is the first thing visitors see on your homepage."
        }),
    )
    
    readonly_fields = ("updated_at",)
    
    def has_add_permission(self, request):
        """Only allow one instance"""
        if CompanySettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to the single settings instance if it exists"""
        if CompanySettings.objects.exists():
            obj = CompanySettings.objects.first()
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('admin:company_settings_companysettings_change', args=[obj.pk]))
        return super().changelist_view(request, extra_context)
    
    def get_form(self, request, obj=None, **kwargs):
        """Add help text to the form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add placeholder text for CTA URL
        if 'hero_cta_url' in form.base_fields:
            form.base_fields['hero_cta_url'].help_text += " Examples: members:membership_plans, products:list, core:contact (use full namespace)"
        
        return form
