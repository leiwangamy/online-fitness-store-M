from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def health_check(request):
    """Simple health check endpoint for nginx/gunicorn monitoring"""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("health/", health_check, name="health"),
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

    path("cart/", include(("cart.urls", "cart"), namespace="cart")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("payment/", include(("payment.urls", "payment"), namespace="payment")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
