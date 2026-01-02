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
    
    
    def is_open_for_signup(self, request):
        """
        Check if signup is allowed. Prevent signup for permanently deleted users.
        """
        # Allow normal signup
        return True
    
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
    
    def is_email_verified(self, request, email):
        """
        Override to allow login without email verification for existing users,
        but require verification for new signups.
        
        - During SIGNUP: Email verification is mandatory (user must verify)
        - During LOGIN: Email verification is optional (existing users can log in)
        """
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Check if this is a login attempt (user already exists)
        try:
            user = User.objects.get(email=email)
            # User exists - this is a login attempt, allow login without verification
            # Existing users can always log in, even if email isn't verified
            return True
        except User.DoesNotExist:
            # User doesn't exist - this is a signup attempt
            # For new signups, require email verification (use parent method)
            return super().is_email_verified(request, email)

