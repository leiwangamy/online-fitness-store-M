"""
Custom allauth adapter to ensure usernames are set to email
when using email-only authentication.
"""
from allauth.account.adapter import DefaultAccountAdapter


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

