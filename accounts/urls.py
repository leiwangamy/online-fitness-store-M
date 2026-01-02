from django.urls import path
from . import views

app_name = "accounts"   # 👈 namespace

urlpatterns = [
    path("settings/", views.account_settings, name="account_settings"),
    path("password/change/", views.password_change, name="password_change"),
    path("delete/", views.delete_account, name="delete_account"),
    path("recover/", views.recover_account, name="recover_account"),
    path("logout/", views.logout_view, name="account_logout"),
    path("test-email-confirm/", views.test_email_confirm, name="test_email_confirm"),  # Test view - only works in DEBUG mode
    # Signup is handled by django-allauth at /accounts/signup/ (account_signup)
    # path("signup/", views.signup, name="signup"),  # Disabled - using allauth signup
]
