import os
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.static import serve
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.admin_views import toggle_platform_membership, toggle_seller_membership, backup_database

# Ensure all admin.py files are discovered
admin.autodiscover()


def health_check(request):
    """Simple health check endpoint for nginx/gunicorn monitoring"""
    return HttpResponse(b"ok", content_type="text/plain")


@require_http_methods(["GET", "POST"])
@csrf_exempt
def admin_logout(request):
    """Custom admin logout view that handles both GET and POST without CSRF issues"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("admin:index")


urlpatterns = [
    path("health/", health_check, name="health"),
    path("admin/logout/", admin_logout, name="admin_logout"),
    path("admin/toggle-platform-membership/", toggle_platform_membership, name="admin_toggle_platform_membership"),
    path("admin/toggle-seller-membership/", toggle_seller_membership, name="admin_toggle_seller_membership"),
    path("admin/backup-database/", backup_database, name="admin_backup_database"),
    path("admin/", admin.site.urls),

    # Include accounts app first so it can override allauth URLs (accessed with namespace "accounts")
    # Then include allauth for login/signup etc. (accessed without namespace as 'account_login', 'account_signup')
    # Django processes URLs in order, so accounts URLs are checked first for matches
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("allauth.urls")),

    # home page
    path("", include(("home.urls", "home"), namespace="home")),

    # products
    path("products/", include(("products.urls", "products"), namespace="products")),

    # membership
    path("", include(("members.urls", "members"), namespace="members")),

    # profile app (NOTE: app is "profiles")
    path("profiles/", include(("profiles.urls", "profiles"), namespace="profiles")),
    
    # core app (contact page)
    path("", include(("core.urls", "core"), namespace="core")),

    path("cart/", include(("cart.urls", "cart"), namespace="cart")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("payment/", include(("payment.urls", "payment"), namespace="payment")),
    
    # sellers app
    path("seller/", include(("sellers.urls", "sellers"), namespace="sellers")),
    
    # API endpoints - centralized in api app
    path("api/", include("api.urls")),
]

# Serve media files (in production, consider using nginx or a CDN)
# For now, serving media files directly through Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve media files (can be replaced with nginx later)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
