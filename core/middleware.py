"""
Middleware to ensure Site with SITE_ID exists before any view runs.
Fixes 500 on /admin/login/ when DB wasn't ready at app startup.
"""
import logging
import os
import traceback

logger = logging.getLogger(__name__)
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


def log_500_traceback_middleware(get_response):
    """Log full traceback when a view raises (so admin 500 shows real cause in console)."""
    def middleware(request):
        try:
            return get_response(request)
        except Exception:
            logger.exception("Unhandled exception for %s %s", request.method, request.path)
            traceback.print_exc()
            raise
    return middleware
