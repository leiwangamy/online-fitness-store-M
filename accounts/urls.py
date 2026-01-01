from django.urls import path
from . import views

app_name = "accounts"   # 👈 namespace

urlpatterns = [
    path("settings/", views.account_settings, name="account_settings"),
    path("logout/", views.logout_view, name="account_logout"),
    # Signup is handled by django-allauth at /accounts/signup/ (account_signup)
    # path("signup/", views.signup, name="signup"),  # Disabled - using allauth signup
]
