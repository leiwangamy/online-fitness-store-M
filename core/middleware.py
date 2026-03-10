"""
Middleware to ensure Site with SITE_ID exists before any view runs.
Fixes 500 on /admin/login/ when DB wasn't ready at app startup.
"""
import os

_site_ensured = False


def ensure_site_middleware(get_response):
    def middleware(request):
        global _site_ensured
        if not _site_ensured:
            try:
                from django.contrib.sites.models import Site
                from django.conf import settings
                domain = (os.environ.get("SITE_DOMAIN") or getattr(settings, "SITE_DOMAIN", "store.lwsoc.com") or "store.lwsoc.com").strip()
                name = (os.environ.get("SITE_NAME") or domain).strip() or domain
                site, _ = Site.objects.get_or_create(pk=settings.SITE_ID, defaults={"domain": domain, "name": name})
                site.domain = domain
                site.name = name
                site.save(update_fields=["domain", "name"])
            except Exception:
                pass
            _site_ensured = True
        return get_response(request)
    return middleware
