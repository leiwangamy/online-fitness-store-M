from .models import CompanySettings


def company_settings(request):
    """
    Context processor to make company settings available in all templates.
    Usage in templates: {{ company_settings.company_name }}
    """
    try:
        return {
            'company_settings': CompanySettings.get_settings()
        }
    except Exception:
        # Avoid 500 on admin/login or any page if DB is unavailable or table missing
        class DefaultCompanySettings:
            company_name = "Fitness Store"
            support_email = ""
            phone_number = ""
            address = ""
            logo = None
            favicon = None
            tagline = ""
            pickup_only = False
            shipping_policy = ""
            hero_title = ""
            hero_subtitle = ""
            hero_cta_text = ""
            hero_cta_url = ""
            hero_image = None
            updated_at = None
        return {'company_settings': DefaultCompanySettings()}

