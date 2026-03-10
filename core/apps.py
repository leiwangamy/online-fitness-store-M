# core/apps.py
import os
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Ensure Site with SITE_ID=1 exists (avoids 500 on admin/login when Django/allauth resolve current site)
        try:
            from django.contrib.sites.models import Site
            domain = (os.environ.get("SITE_DOMAIN") or "store.lwsoc.com").strip() or "store.lwsoc.com"
            name = (os.environ.get("SITE_NAME") or domain).strip() or domain
            site, created = Site.objects.get_or_create(pk=1, defaults={"domain": domain, "name": name})
            site.domain = domain
            site.name = name
            site.save(update_fields=["domain", "name"])
        except Exception:
            pass

        # Attach the CSV action to all registered ModelAdmins
        from django.contrib import admin
        from .admin_actions import export_selected_as_csv

        for model, model_admin in admin.site._registry.items():
            existing = list(getattr(model_admin, "actions", []) or [])
            if export_selected_as_csv not in existing:
                model_admin.actions = existing + [export_selected_as_csv]
