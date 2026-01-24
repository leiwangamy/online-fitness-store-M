from django.db import models
from django.core.exceptions import ValidationError


class CompanySettings(models.Model):
    """
    Global site settings for company branding and hero section.
    Only one instance should exist.
    """
    # Company Branding
    company_name = models.CharField(max_length=255, default="Fitness Store")
    logo = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Company logo")
    favicon = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Browser favicon (optional)")
    tagline = models.CharField(max_length=255, blank=True, help_text="Company tagline or slogan")
    
    # Contact Information
    support_email = models.EmailField(blank=True, help_text="Support/contact email")
    phone_number = models.CharField(max_length=50, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Physical address")
    
    # Order Settings
    pickup_only = models.BooleanField(default=False, help_text="If enabled, only pickup orders are allowed. Shipping address will be hidden and only the first pickup location will be shown.")
    shipping_policy = models.TextField(blank=True, help_text="Shipping policy text displayed on cart page. Leave blank to hide.")
    
    # Hero Section
    hero_title = models.CharField(max_length=120, blank=True, help_text="Main hero headline (max 120 chars)")
    hero_subtitle = models.TextField(max_length=500, blank=True, help_text="Hero subtitle/description (max 500 chars)")
    hero_cta_text = models.CharField(max_length=50, blank=True, help_text="Call-to-action button text (e.g., 'Get Started')")
    hero_cta_url = models.CharField(max_length=255, blank=True, help_text="CTA button URL or Django URL name (e.g., 'membership_plans')")
    hero_image = models.ImageField(upload_to='hero/', blank=True, null=True, help_text="Hero section background image")
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Settings"
        verbose_name_plural = "Company Settings"
    
    def __str__(self):
        return self.company_name
    
    def clean(self):
        """Enforce single-row constraint"""
        if CompanySettings.objects.exists() and not self.pk:
            raise ValidationError("Only one CompanySettings instance is allowed. Please edit the existing settings.")
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk and CompanySettings.objects.exists():
            raise ValidationError("Only one CompanySettings instance is allowed.")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the single settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
