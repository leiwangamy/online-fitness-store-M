from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication (email login via allauth)
    path("accounts/", include("allauth.urls")),

    # App routes
    path("payment/", include("payment.urls")),
    path("", include("members.urls")),  # homepage + member pages
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
