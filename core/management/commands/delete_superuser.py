"""
Django management command to delete a superuser by email.
Usage: python manage.py delete_superuser leiwasoc@gmail.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete a superuser by email address'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the superuser to delete')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write("=" * 60)
        self.stdout.write("CURRENT DATABASE CONNECTION")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Database: {connection.settings_dict['NAME']}")
        self.stdout.write(f"User: {connection.settings_dict['USER']}")
        self.stdout.write(f"Host: {connection.settings_dict['HOST']}")
        self.stdout.write()
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"DELETING SUPERUSER: {email}")
        self.stdout.write("=" * 60)
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(self.style.SUCCESS(f"Found user:"))
            self.stdout.write(f"  - Username: {user.username}")
            self.stdout.write(f"  - Email: {user.email}")
            self.stdout.write(f"  - Is Superuser: {user.is_superuser}")
            self.stdout.write(f"  - Is Staff: {user.is_staff}")
            self.stdout.write(f"  - Date Joined: {user.date_joined}")
            self.stdout.write()
            
            # Check for related objects
            try:
                from sellers.models import Seller
                from allauth.account.models import EmailAddress
                
                has_seller = Seller.objects.filter(user=user).exists()
                has_email_address = EmailAddress.objects.filter(user=user).exists()
                
                if has_seller:
                    seller = Seller.objects.get(user=user)
                    self.stdout.write(f"  - Has Seller Profile: Yes (display_name: {seller.display_name})")
                else:
                    self.stdout.write(f"  - Has Seller Profile: No")
                
                if has_email_address:
                    email_addrs = EmailAddress.objects.filter(user=user)
                    self.stdout.write(f"  - Has EmailAddress records: Yes ({email_addrs.count()})")
                else:
                    self.stdout.write(f"  - Has EmailAddress records: No")
            except ImportError:
                pass  # Related apps might not be installed
            
            self.stdout.write()
            self.stdout.write("Deleting user and all related objects...")
            
            # Delete the user (this will cascade delete related objects if foreign keys are set to CASCADE)
            user.delete()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted user: {email}"))
            self.stdout.write()
            
            # Verify deletion
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING("WARNING: User still exists in database!"))
            else:
                self.stdout.write(self.style.SUCCESS("User confirmed deleted from database."))
            
            # Show remaining superusers
            remaining_superusers = User.objects.filter(is_superuser=True)
            count = remaining_superusers.count()
            self.stdout.write()
            self.stdout.write(f"Remaining superusers: {count}")
            if count > 0:
                self.stdout.write("Remaining superusers:")
                for su in remaining_superusers:
                    self.stdout.write(f"  - {su.username} ({su.email})")

        except User.DoesNotExist:
            raise CommandError(f"User with email '{email}' not found in database.")
        except Exception as e:
            raise CommandError(f"Failed to delete user: {e}")

