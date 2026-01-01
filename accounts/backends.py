"""
Custom authentication backend to prevent soft-deleted users from logging in.
Note: This backend runs AFTER allauth's backend, so it only checks soft deletion
for users authenticated by ModelBackend (admin, etc.), not email auth handled by allauth.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from core.models import UserDeletion

User = get_user_model()


class SoftDeleteAwareBackend(ModelBackend):
    """
    Authentication backend that prevents soft-deleted users from logging in,
    but allows recovery if within the 30-day window.
    This only handles username-based authentication; email auth is handled by allauth.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user, but check if they're soft-deleted first.
        Only handles username-based auth; email auth is handled by allauth backend.
        """
        # Try normal authentication (username-based only)
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is soft-deleted
        try:
            deletion = user.deletion_record
            if deletion.can_recover:
                # User is deleted but can recover - allow login and show recovery message
                return user
            else:
                # Past recovery period - don't allow login
                return None
        except UserDeletion.DoesNotExist:
            # User is not deleted - allow normal login
            return user
    
    def get_user(self, user_id):
        """
        Get user, but return None if permanently deleted.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        # Check if permanently deleted
        try:
            deletion = user.deletion_record
            if not deletion.can_recover:
                return None  # Permanently deleted
        except UserDeletion.DoesNotExist:
            pass  # Not deleted
        
        return user if self.user_can_authenticate(user) else None

