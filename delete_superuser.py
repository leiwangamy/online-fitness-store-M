#!/usr/bin/env python
"""Delete a specific superuser by email from the database"""
import os
import sys
import codecs
import django

# Fix Unicode output for Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Change this email to delete a different superuser
EMAIL = 'leiwasoc@gmail.com'

print("=" * 60)
print("CURRENT DATABASE CONNECTION")
print("=" * 60)
print(f"Database: {connection.settings_dict['NAME']}")
print(f"User: {connection.settings_dict['USER']}")
print(f"Host: {connection.settings_dict['HOST']}")
print()

print("=" * 60)
print(f"DELETING SUPERUSER: {EMAIL}")
print("=" * 60)

try:
    user = User.objects.get(email=EMAIL)
    
    print(f"Found user:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - Is Superuser: {user.is_superuser}")
    print(f"  - Is Staff: {user.is_staff}")
    print(f"  - Date Joined: {user.date_joined}")
    print()
    
    # Check for related objects
    try:
        from sellers.models import Seller
        from allauth.account.models import EmailAddress
        
        has_seller = Seller.objects.filter(user=user).exists()
        has_email_address = EmailAddress.objects.filter(user=user).exists()
        
        if has_seller:
            seller = Seller.objects.get(user=user)
            print(f"  - Has Seller Profile: Yes (display_name: {seller.display_name})")
        else:
            print(f"  - Has Seller Profile: No")
        
        if has_email_address:
            email_addrs = EmailAddress.objects.filter(user=user)
            print(f"  - Has EmailAddress records: Yes ({email_addrs.count()})")
        else:
            print(f"  - Has EmailAddress records: No")
    except ImportError:
        pass  # Related apps might not be installed
    
    print()
    print("Deleting user and all related objects...")
    
    # Delete the user (this will cascade delete related objects if foreign keys are set to CASCADE)
    user.delete()
    
    print(f"[OK] Successfully deleted user: {EMAIL}")
    print()
    
    # Verify deletion
    if User.objects.filter(email=EMAIL).exists():
        print("[WARNING] User still exists in database!")
    else:
        print("[OK] User confirmed deleted from database.")
    
    # Show remaining superusers
    remaining_superusers = User.objects.filter(is_superuser=True)
    count = remaining_superusers.count()
    print()
    print(f"Remaining superusers: {count}")
    if count > 0:
        print("Remaining superusers:")
        for su in remaining_superusers:
            print(f"  - {su.username} ({su.email})")

except User.DoesNotExist:
    print(f"[ERROR] User with email '{EMAIL}' not found in database.")
    print()
    
    # Show all superusers
    superusers = User.objects.filter(is_superuser=True)
    count = superusers.count()
    print(f"Current superusers in database ({count}):")
    for su in superusers:
        print(f"  - {su.username} ({su.email})")
    sys.exit(1)

except Exception as e:
    print(f"[ERROR] Failed to delete user: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
