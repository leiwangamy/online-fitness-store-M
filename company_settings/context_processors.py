from .models import CompanySettings


def company_settings(request):
    """
    Context processor to make company settings available in all templates.
    Usage in templates: {{ company_settings.company_name }}
    """
    return {
        'company_settings': CompanySettings.get_settings()
    }

