# Enable Email Verification - Step by Step Guide

## Overview
This guide will help you enable email verification for new user signups using your Google Workspace email (`info@lwsoc.com`).

## Step 1: Update `.env` file on EC2

SSH into your EC2 instance and edit the `.env` file:

```bash
cd ~/online-fitness-store-P
nano .env
```

## Step 2: Update these settings in `.env`

Make sure your `.env` file has these settings:

```bash
# Set DEBUG to 0 for production (this enables SMTP email backend)
DJANGO_DEBUG=0

# Enable email verification (mandatory means users must verify before login)
ACCOUNT_EMAIL_VERIFICATION=mandatory

# Remove or comment out the EMAIL_BACKEND override (let Django use SMTP in production)
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMTP Settings for Google Workspace
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=info@lwsoc.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=Fitness Club <info@lwsoc.com>
```

## Step 3: Get Google App Password

If you haven't already, you need to create an App Password for your Google Workspace account:

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (must be enabled)
3. Scroll down to **App passwords**
4. Create a new app password for "Mail"
5. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)
6. Use this password (without spaces) in `EMAIL_HOST_PASSWORD` in your `.env` file

**Important:** Use the App Password, NOT your regular Google account password.

## Step 4: Pull latest code changes

The code changes include a custom adapter to ensure usernames match emails:

```bash
cd ~/online-fitness-store-P
git pull origin main  # or your branch name
```

## Step 5: Restart Docker containers

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

## Step 6: Verify email settings

Test that Django can see your email configuration:

```bash
docker compose -f docker-compose.prod.yml exec web python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')
import django
django.setup()
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ACCOUNT_EMAIL_VERIFICATION:', getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'NOT SET'))
print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
print('EMAIL_HOST:', getattr(settings, 'EMAIL_HOST', 'NOT SET'))
print('EMAIL_HOST_USER:', getattr(settings, 'EMAIL_HOST_USER', 'NOT SET'))
print('EMAIL_HOST_PASSWORD:', 'SET' if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'NOT SET')
print('DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL)
"
```

Expected output:
- `DEBUG: False`
- `ACCOUNT_EMAIL_VERIFICATION: mandatory`
- `EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST: smtp.gmail.com`
- `EMAIL_HOST_USER: info@lwsoc.com`
- `EMAIL_HOST_PASSWORD: SET`
- `DEFAULT_FROM_EMAIL: Fitness Club <info@lwsoc.com>`

## Step 7: Test email sending

Test that emails can be sent:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

Then in the Python shell:

```python
from django.core.mail import send_mail
from django.conf import settings

try:
    send_mail(
        'Test Email',
        'This is a test email from your Django app.',
        settings.DEFAULT_FROM_EMAIL,
        ['your-test-email@example.com'],  # Use your own email for testing
        fail_silently=False,
    )
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error sending email: {e}")
```

## Step 8: Test signup flow

1. Go to your signup page: `http://15.223.56.68:8000/accounts/signup/`
2. Enter an email address and password
3. Submit the form
4. Check the email inbox for the verification email
5. Click the verification link in the email
6. You should be automatically logged in

## Troubleshooting

### Email not sending?
- Check that `EMAIL_HOST_PASSWORD` is the App Password (not your regular password)
- Verify 2-Step Verification is enabled on your Google account
- Check Docker logs: `docker compose -f docker-compose.prod.yml logs web --tail=50`

### Username not matching email?
- The custom adapter should handle this automatically
- If issues persist, check that `ACCOUNT_USERNAME_REQUIRED = False` in settings

### Still seeing console email backend?
- Make sure `DJANGO_DEBUG=0` in `.env`
- Make sure `EMAIL_BACKEND` is not set in `.env` (or is commented out)
- Restart containers: `docker compose -f docker-compose.prod.yml restart web`

## What Changed in the Code

1. **Created `accounts/adapters.py`**: Custom adapter that sets username to email when creating users
2. **Updated `settings.py`**: Added `ACCOUNT_ADAPTER = "accounts.adapters.CustomAccountAdapter"`

This ensures that when users sign up with email-only authentication, their username field will automatically be set to their email address for consistency.

