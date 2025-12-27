# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Attach the CSV action to all registered ModelAdmins
        from django.contrib import admin
        from .admin_actions import export_selected_as_csv

        for model, model_admin in admin.site._registry.items():
            existing = list(getattr(model_admin, "actions", []) or [])
            if export_selected_as_csv not in existing:
                model_admin.actions = existing + [export_selected_as_csv]
