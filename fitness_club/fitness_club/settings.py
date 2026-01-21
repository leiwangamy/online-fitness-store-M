"""
Django Settings Module for Online Fitness Store

This module contains all Django configuration settings for the e-commerce platform.

Key Configuration Areas:
1. Security: SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
2. Database: PostgreSQL for production, SQLite for development
3. Installed Apps: All Django apps used in the project
4. Middleware: Security, authentication, session management
5. Static/Media Files: File serving configuration
6. Authentication: Django Allauth configuration
7. Email: Email backend for verification and notifications
8. Internationalization: Language and timezone settings

Environment Variables:
- DJANGO_SECRET_KEY: Secret key for cryptographic signing (REQUIRED)
- DJANGO_DEBUG: Debug mode (1 for dev, 0 for production)
- ALLOWED_HOSTS: Comma-separated list of allowed hostnames
- CSRF_TRUSTED_ORIGINS: Comma-separated list of trusted origins
- Database credentials: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, POSTGRES_PORT

Production Considerations:
- Set DEBUG=False
- Use strong SECRET_KEY
- Configure proper ALLOWED_HOSTS
- Set up SSL/HTTPS
- Use production database (PostgreSQL)
- Configure production email backend
- Set up proper static file serving (Nginx/WhiteNoise)

Development:
- DEBUG=True
- SQLite database (or local PostgreSQL)
- Console email backend
- Local file serving
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
# Your project is nested like: root/fitness_club/fitness_club/settings.py
# so parent.parent.parent points to the repo root (where /templates, /static live)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root
load_dotenv(BASE_DIR / ".env")  # loads your .env from project root

# ------------------------------------------------------------
# Core settings
# ------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# ALLOWED_HOSTS from environment variable (comma-separated)
# Example: ALLOWED_HOSTS=ec2-15-223-56-68.ca-central-1.compute.amazonaws.com,example.com
allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
    # Always include localhost and 127.0.0.1 for health checks and local access
    if "localhost" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append("localhost")
    if "127.0.0.1" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append("127.0.0.1")
else:
    # Default for local development
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# CSRF_TRUSTED_ORIGINS from environment variable (comma-separated)
# Example: CSRF_TRUSTED_ORIGINS=https://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com,https://example.com
csrf_origins_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_env.split(",") if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# Replit support (safe locally)
replit_domains = os.environ.get("REPLIT_DOMAINS")
if replit_domains:
    domain_list = [d.strip() for d in replit_domains.split(",") if d.strip()]
    ALLOWED_HOSTS += domain_list
    CSRF_TRUSTED_ORIGINS += [f"https://{d}" for d in domain_list]

# ------------------------------------------------------------
# Applications
# ------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Third-party
    "rest_framework",
    "rest_framework.authtoken",  # Token authentication for API
    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    # your apps
    "home",
    "products",
    "cart",
    "orders",
    "payment",
    "members",
    "accounts",
    "core",
    "api",  # API app - central hub for all API endpoints
    "profiles.apps.ProfilesConfig",
    "sellers.apps.SellersConfig",

]

# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # required for django-allauth
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ------------------------------------------------------------
# URLs / WSGI / ASGI
# ------------------------------------------------------------
ROOT_URLCONF = "fitness_club.fitness_club.urls"
WSGI_APPLICATION = "fitness_club.fitness_club.wsgi.application"
ASGI_APPLICATION = "fitness_club.fitness_club.asgi.application"

# ------------------------------------------------------------
# Templates
# ------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # required for allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "members.context_processors.membership_context",
                "cart.context_processors.cart_context",
                "orders.context_processors.staff_notifications",  # Staff notifications (refund requests)
                "core.context_processors.admin_settings",  # Admin settings (membership visibility toggle)
                "core.context_processors.membership_availability",  # Membership availability (for navigation)
            ],
        },
    },
]

# ------------------------------------------------------------
# Database
# ------------------------------------------------------------
# PostgreSQL Database Configuration
# This points to the fitness_m_user database (the new database)
# The .env file should have: POSTGRES_DB=fitness_m_user, POSTGRES_USER=fitness_m
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "fitness_m_user"),
        "USER": os.environ.get("POSTGRES_USER", "fitness_m"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,  # Force connections to close immediately (no persistent connections)
    }
}


# ------------------------------------------------------------
# Auth / Allauth
# ------------------------------------------------------------
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "allauth.account.auth_backends.AuthenticationBackend",  # Allauth backend first for email auth
    "accounts.backends.SoftDeleteAwareBackend",  # Custom backend that handles soft-deleted users
    "django.contrib.auth.backends.ModelBackend",
]

# Modern allauth settings (Django 5+)
# Note: Some settings show deprecation warnings but are needed for compatibility
ACCOUNT_AUTHENTICATION_METHOD = "email"  # Use email for authentication
ACCOUNT_EMAIL_REQUIRED = True  # Required when using email authentication
ACCOUNT_UNIQUE_EMAIL = True  # Required when login isn't username-only
ACCOUNT_USERNAME_REQUIRED = False  # Username not required when using email
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# Custom adapter to ensure username is set to email
ACCOUNT_ADAPTER = "accounts.adapters.CustomAccountAdapter"

# Redirects
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

# ------------------------------------------------------------
# Email
# ------------------------------------------------------------
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Fitness Club <no-reply@lwsoc.com>"
)

# Email verification settings
# "mandatory" = email verification required for new signups
# We override is_email_verified() in adapter to allow login without verification for existing users
ACCOUNT_EMAIL_VERIFICATION = os.environ.get("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
# When email verification is mandatory, users are NOT auto-logged in after signup
# They must verify their email first, then they'll be logged in after confirmation
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  # Auto-login AFTER email confirmation
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True  # Redirect authenticated users
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/"  # Redirect to home after email confirmation
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/"  # Redirect to home if already logged in
# Allow email confirmation for anonymous users (don't require login to confirm email)
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True  # Use HMAC for email confirmation keys (more secure)

# Choose backend based on DEBUG or EMAIL_BACKEND env var
# Allow overriding email backend via environment variable for testing
email_backend_override = os.environ.get("EMAIL_BACKEND", "")
if email_backend_override:
    EMAIL_BACKEND = email_backend_override
elif DEBUG:
    # Dev: print emails to console (you'll see the verification link in logs)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

    EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_TIMEOUT = 10  # Timeout in seconds for SMTP connection

    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise ValueError("Only one of EMAIL_USE_TLS or EMAIL_USE_SSL can be True.")



# ------------------------------------------------------------
# Password validation
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Static / Media
# ------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # For production (collectstatic)

# WhiteNoise configuration for serving static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------
# Django REST Framework Configuration
# ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
