#!/usr/bin/env python
"""Delete all superusers from the database"""
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

print("=" * 60)
print("CURRENT DATABASE CONNECTION")
print("=" * 60)
print(f"Database: {connection.settings_dict['NAME']}")
print(f"User: {connection.settings_dict['USER']}")
print(f"Host: {connection.settings_dict['HOST']}")
print()

print("=" * 60)
print("DELETING ALL SUPERUSERS")
print("=" * 60)

superusers = User.objects.filter(is_superuser=True)
count = superusers.count()
print(f"Found {count} superuser(s):")
for su in superusers:
    print(f"  - {su.username} ({su.email})")

print()
print("Deleting...")
superusers.delete()

remaining = User.objects.filter(is_superuser=True).count()
print(f"Deleted {count} superuser(s).")
print(f"Remaining superusers: {remaining}")
print()

if remaining == 0:
    print("[OK] All superusers deleted successfully!")
    print()
    print("Next step: Create a new superuser by running:")
    print("  python manage.py createsuperuser")
else:
    print("[WARNING] Some superusers still exist!")
