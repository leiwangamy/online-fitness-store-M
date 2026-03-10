from django.apps import AppConfig


class CompanySettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'company_settings'
    verbose_name = 'Company Settings'

    def ready(self):
        """Use Company Settings Support email for sending when not set in .env."""
        import os
        from django.conf import settings as django_settings
        try:
            company = self.get_model("CompanySettings").get_settings()
            support_email = (getattr(company, "support_email", None) or "").strip()
            company_name = getattr(company, "company_name", None) or "Fitness Store"
            if not os.environ.get("DEFAULT_FROM_EMAIL") and support_email:
                django_settings.DEFAULT_FROM_EMAIL = f"{company_name} <{support_email}>"
            if not os.environ.get("EMAIL_HOST_USER") and support_email:
                django_settings.EMAIL_HOST_USER = support_email
        except Exception:
            pass
        if not getattr(django_settings, "DEFAULT_FROM_EMAIL", None):
            django_settings.DEFAULT_FROM_EMAIL = "Fitness Store <noreply@example.com>"
