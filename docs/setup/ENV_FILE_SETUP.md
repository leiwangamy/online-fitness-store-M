# Environment File Setup for EC2

## Required Settings in `.env` File

To ensure email verification works correctly (mandatory for signup, optional for login), your `.env` file on EC2 should have:

```bash
# Email Verification
# Set to "mandatory" to require email verification for new signups
# Existing users can still log in without verification (handled by adapter)
ACCOUNT_EMAIL_VERIFICATION=mandatory
```

## Complete `.env` File Template

Here's what your `.env` file should look like on EC2:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=0

# Allowed Hosts (comma-separated, no spaces after commas)
ALLOWED_HOSTS=15.223.56.68,ec2-15-223-56-68.ca-central-1.compute.amazonaws.com,localhost

# CSRF Trusted Origins (comma-separated, include https:// if you have SSL)
# CSRF_TRUSTED_ORIGINS=https://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com

# Database Configuration (for Docker)
POSTGRES_DB=fitness_club_db
POSTGRES_USER=fitness_user
POSTGRES_PASSWORD=your-database-password
DB_HOST=db
POSTGRES_PORT=5432

# Email Verification
# "mandatory" = new signups must verify email, but existing users can log in
ACCOUNT_EMAIL_VERIFICATION=mandatory

# Email settings for production (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=info@lwsoc.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=Fitness Club <info@lwsoc.com>
```

## How to Update `.env` on EC2

1. SSH into your EC2 instance:
   ```bash
   ssh -i ~/Downloads/fitness-key.pem ubuntu@15.223.56.68
   ```

2. Edit the `.env` file:
   ```bash
   cd ~/online-fitness-store-M
   nano .env
   ```

3. Make sure this line exists (or add it):
   ```bash
   ACCOUNT_EMAIL_VERIFICATION=mandatory
   ```

4. Save and exit (Ctrl+X, then Y, then Enter)

5. Verify the setting is correct:
   ```bash
   grep ACCOUNT_EMAIL_VERIFICATION .env
   ```
   This should show: `ACCOUNT_EMAIL_VERIFICATION=mandatory`

6. Restart the container to apply changes:
   ```bash
   docker compose -f docker-compose.prod.yml restart web
   ```

7. Verify the setting is loaded in Django:
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py shell
   ```
   Then in the Python shell:
   ```python
   from django.conf import settings
   print(f"ACCOUNT_EMAIL_VERIFICATION: {settings.ACCOUNT_EMAIL_VERIFICATION}")
   ```
   This should print: `ACCOUNT_EMAIL_VERIFICATION: mandatory`
   Type `exit()` to leave the shell.

## How It Works

- **New Signups**: Must verify email before they can use the account (mandatory)
- **Existing Users**: Can log in immediately with email and password (no verification required)
- **After Email Confirmation**: Users are automatically logged in

This is handled by the custom adapter which checks if a user already exists in the database.

