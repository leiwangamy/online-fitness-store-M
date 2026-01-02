from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login

from .forms import AccountEmailForm, ProfileForm, CustomPasswordChangeForm, AccountDeletionForm
from profiles.models import Profile
from core.models import UserDeletion
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

def signup(request):
    # (Not used if allauth handles signup)
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("home:home")
    else:
        form = UserCreationForm()
    return render(request, "account/signup.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("home:home")


@login_required
def account_settings(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        email_form = AccountEmailForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if email_form.is_valid() and profile_form.is_valid():
            email_form.save()
            profile_form.save()
            messages.success(request, "Your account info has been updated.")
            return redirect("accounts:account_settings")
    else:
        email_form = AccountEmailForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "account/account_settings.html", {
        "email_form": email_form,
        "profile_form": profile_form,
    })


@login_required
def password_change(request):
    """Allow users to change their password"""
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important: keeps user logged in
            messages.success(request, "Your password has been successfully changed.")
            return redirect("accounts:password_change")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, "account/password_change.html", {
        "form": form
    })


@login_required
def delete_account(request):
    """Soft delete user account with 30-day recovery period"""
    user = request.user
    
    # Check if account is already deleted
    if hasattr(user, 'deletion_record'):
        messages.warning(request, "Your account is already scheduled for deletion.")
        return redirect("accounts:account_settings")
    
    if request.method == "POST":
        form = AccountDeletionForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            # Create deletion record
            UserDeletion.objects.create(
                user=user,
                reason=form.cleaned_data.get('reason', '')
            )
            # Log out the user
            logout(request)
            messages.success(
                request,
                "Your account has been scheduled for deletion. You can recover it within 30 days by logging in."
            )
            return redirect("home:home")
    else:
        form = AccountDeletionForm()
    
    return render(request, "account/delete_account.html", {
        "form": form
    })


@login_required
def recover_account(request):
    """Recover a soft-deleted account"""
    user = request.user
    
    if not hasattr(user, 'deletion_record'):
        messages.info(request, "Your account is not scheduled for deletion.")
        return redirect("accounts:account_settings")
    
    deletion = user.deletion_record
    
    if not deletion.can_recover:
        messages.error(
            request,
            "The 30-day recovery period has expired. Your account cannot be recovered."
        )
        return redirect("home:home")
    
    if request.method == "POST":
        # Delete the deletion record to restore the account
        deletion.delete()
        messages.success(request, "Your account has been successfully recovered!")
        return redirect("accounts:account_settings")
    
    return render(request, "account/recover_account.html", {
        "deletion": deletion,
        "days_remaining": deletion.days_until_permanent
    })


def test_email_confirm(request):
    """
    Test view to preview the email confirmation page.
    Only works in DEBUG mode for safety.
    Access at: /accounts/test-email-confirm/
    """
    if not settings.DEBUG:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("This view is only available in DEBUG mode.")
    
    # Create a simple mock confirmation object for preview
    class MockEmailAddress:
        def __init__(self):
            self.email = "test@example.com"
    
    class MockConfirmation:
        def __init__(self):
            self.email_address = MockEmailAddress()
            self.key = "test-key-123"
    
    # Create mock confirmation object
    confirmation = MockConfirmation()
    
    return render(request, "account/email_confirm.html", {
        "confirmation": confirmation
    })