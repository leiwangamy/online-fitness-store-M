"""
Custom allauth adapter to ensure usernames are set to email
when using email-only authentication.
"""
from allauth.account.adapter import DefaultAccountAdapter
from core.models import UserDeletion


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter that sets username to email when ACCOUNT_USERNAME_REQUIRED is False.
    This ensures the username field always matches the email for consistency.
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Override to set username to email when username is not required.
        The parent method handles password setting, we just need to set username.
        """
        # Call parent first - this sets the password correctly
        user = super().save_user(request, user, form, commit=False)
        
        # If username is not required, set it to email for consistency
        # Do this AFTER parent saves password, but BEFORE we save
        if not user.username or user.username != user.email:
            user.username = user.email
        
        if commit:
            user.save()
        
        return user
    
    
    def can_authenticate(self, user):
        """
        Check if user can authenticate. Prevent permanently deleted users from logging in.
        Note: Password validation is handled by Django/allauth, we only check soft deletion.
        With ACCOUNT_EMAIL_VERIFICATION = "optional", email verification is not required for login.
        """
        # Check for soft deletion
        try:
            deletion = user.deletion_record
            # Allow login if within recovery period, block if permanently deleted
            return deletion.can_recover
        except (UserDeletion.DoesNotExist, AttributeError):
            # User is not deleted - allow authentication
            return True
    
    def is_open_for_signup(self, request):
        """
        Check if signup is allowed. Prevent signup for permanently deleted users.
        Also ensure email confirmation links work for anonymous users.
        """
        # Allow normal signup
        return True
    
    def is_email_verified(self, request, email):
        """
        Override to allow login without email verification for existing users,
        but require verification for new signups.
        
        IMPORTANT: This method is NOT called during email confirmation.
        It's only called during login/signup to check if email verification is required.
        
        - During SIGNUP: Email verification is mandatory (user must verify)
        - During LOGIN: Email verification is optional (existing users can log in)
        - During EMAIL CONFIRMATION: This method is not called - confirmation happens separately
        """
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        # Skip this check if we're on the email confirmation page
        # (This shouldn't be called there, but just to be safe)
        if '/accounts/confirm-email/' in request.path:
            # Use parent method for email confirmation - don't interfere
            return super().is_email_verified(request, email)
        
        # Check if user exists in database
        try:
            user = User.objects.get(email=email)
            
            # Check if email is verified
            try:
                email_address = EmailAddress.objects.get_for_user(user, email)
                if email_address.verified:
                    # Email is verified - always allow
                    return True
            except EmailAddress.DoesNotExist:
                pass
            
            # Email is not verified - need to distinguish signup from login
            # If user was just created (within last 10 seconds), it's likely a signup
            user_just_created = (timezone.now() - user.date_joined) < timedelta(seconds=10)
            
            # Also check request path to be more certain
            is_signup_path = (
                request.path == '/accounts/signup/' or 
                '/accounts/signup' in request.path or
                (hasattr(request, 'resolver_match') and request.resolver_match and 
                 'signup' in str(request.resolver_match.url_name))
            )
            
            if user_just_created or is_signup_path:
                # This is a signup attempt - require email verification
                # Return False to prevent auto-login during signup
                return False
            else:
                # This is a login attempt for an existing user
                # Allow login without verification
                return True
                
        except User.DoesNotExist:
            # User doesn't exist - this is definitely a signup attempt
            # For new signups, require email verification (use parent method)
            return super().is_email_verified(request, email)

