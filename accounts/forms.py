from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from profiles.models import Profile

User = get_user_model()

class AccountEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "phone",
            "address1", "address2",
            "city", "province",
            "postal_code", "country",
        )


class CustomPasswordChangeForm(PasswordChangeForm):
    """Password change form with custom styling"""
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your current password'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your new password'
        })
    )


class AccountDeletionForm(forms.Form):
    """Form for confirming account deletion"""
    confirm = forms.BooleanField(
        required=True,
        label="I understand that my account will be deleted and I can recover it within 30 days"
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Optional: Tell us why you\'re deleting your account'
        }),
        label="Reason (Optional)"
    )
