# Account Features Implementation Summary

This document summarizes the new account management features that have been added to the Fitness Club application.

## Features Implemented

### 1. Password Change ✅
- **URL**: `/accounts/password/change/`
- **Access**: Logged-in users only
- **Location**: Available from Account Settings page
- **Features**:
  - Users can change their password
  - Requires current password for security
  - User stays logged in after password change
  - Form validation and error messages

### 2. Soft Delete Account with 30-Day Recovery ✅
- **URLs**: 
  - Delete: `/accounts/delete/`
  - Recover: `/accounts/recover/`
- **Access**: Logged-in users only
- **Features**:
  - Users can request account deletion
  - Account is soft-deleted (not permanently removed)
  - 30-day recovery window
  - Users can log in during recovery period to restore account
  - After 30 days, account is permanently deleted (can be automated via management command)
  - Custom authentication backend prevents permanently deleted users from logging in
  - Warning shown in account settings if account is scheduled for deletion

### 3. Company Contact Information Page ✅
- **URL**: `/contact/`
- **Access**: Public (available to all users)
- **Features**:
  - Displays company phone number (778-238-3371)
  - Displays company email (info@lwsoc.com)
  - Displays company address (if set)
  - Displays company description (if set)
  - Editable via Django Admin
  - Link added to main navigation

## Models Created

### `CompanyInfo` (in `core/models.py`)
- Stores company contact information
- Singleton pattern (only one instance)
- Fields:
  - `phone`: Company phone number
  - `email`: Company email address
  - `address`: Company address/description
  - `description`: Additional company information
  - `updated_at`: Last update timestamp

### `UserDeletion` (in `core/models.py`)
- Tracks soft-deleted user accounts
- Fields:
  - `user`: OneToOne relationship to User
  - `deleted_at`: Timestamp when deletion was requested
  - `reason`: Optional reason for deletion
- Properties:
  - `days_until_permanent`: Days remaining until permanent deletion
  - `can_recover`: Boolean indicating if account can be recovered
  - `is_permanent`: Boolean indicating if deletion is permanent

## Authentication Changes

### Custom Authentication Backend
- **File**: `accounts/backends.py`
- **Class**: `SoftDeleteAwareBackend`
- **Purpose**: Prevents permanently deleted users (past 30 days) from logging in
- **Behavior**: Allows soft-deleted users (within 30 days) to log in so they can recover their account

### Settings Update
- Added `accounts.backends.SoftDeleteAwareBackend` to `AUTHENTICATION_BACKENDS`
- This backend runs first to check for soft-deleted accounts

## Admin Interface

### CompanyInfo Admin
- Accessible at `/admin/core/companyinfo/`
- Allows editing company contact information
- Only one instance allowed (singleton pattern)
- Cannot be deleted

### UserDeletion Admin
- Accessible at `/admin/core/userdeletion/`
- View-only interface for monitoring deleted accounts
- Shows deletion date, days remaining, and recovery status
- Cannot manually add deletions (only via user deletion process)

## URLs Added

### Accounts App (`accounts/urls.py`)
- `/accounts/password/change/` - Password change page
- `/accounts/delete/` - Account deletion page
- `/accounts/recover/` - Account recovery page

### Core App (`core/urls.py`)
- `/contact/` - Company contact information page

## Templates Created

1. **`templates/account/password_change.html`** - Password change form
2. **`templates/account/delete_account.html`** - Account deletion confirmation
3. **`templates/account/recover_account.html`** - Account recovery page
4. **`templates/account/account_settings.html`** - Updated account settings with links to new features
5. **`templates/core/contact.html`** - Company contact information page

## Forms Created

1. **`CustomPasswordChangeForm`** - Password change form with custom styling
2. **`AccountDeletionForm`** - Account deletion confirmation form

## Next Steps / Maintenance

### Optional: Permanent Deletion Automation
You may want to create a management command to permanently delete accounts that are past the 30-day recovery period:

```python
# core/management/commands/cleanup_deleted_accounts.py
from django.core.management.base import BaseCommand
from core.models import UserDeletion
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=30)
        permanent_deletions = UserDeletion.objects.filter(
            deleted_at__lt=cutoff_date
        )
        count = permanent_deletions.count()
        for deletion in permanent_deletions:
            deletion.user.delete()  # Permanently delete user
        self.stdout.write(f"Permanently deleted {count} accounts.")
```

Run this command periodically (e.g., via cron) to clean up permanently deleted accounts.

### Initial Company Info Setup
After running migrations, go to Django Admin (`/admin/core/companyinfo/`) to set the initial company contact information:
- Phone: 778-238-3371
- Email: info@lwsoc.com
- Address: (add your company address)
- Description: (add any additional information)

## Testing Checklist

- [ ] Test password change functionality
- [ ] Test account deletion (verify 30-day window)
- [ ] Test account recovery within 30 days
- [ ] Test that permanently deleted accounts cannot log in
- [ ] Test contact page displays correctly
- [ ] Test editing company info in admin
- [ ] Verify all navigation links work correctly

## Migration Required

Don't forget to create and run migrations:

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Notes

- The soft delete system preserves user data for 30 days, allowing recovery
- After 30 days, accounts should be permanently deleted (manual or automated)
- The contact page is publicly accessible
- All new pages match the existing light green theme
- Account settings page now shows a warning if account is scheduled for deletion

