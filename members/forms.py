# members/forms.py

from django import forms
from .models import Product
from django.contrib.auth.models import User
from .models import MemberProfile
from django.contrib.auth import get_user_model 

User = get_user_model()

class ProductAdminForm(forms.ModelForm):
    """
    Custom admin form to make service availability clearer:
    - For service products, you see a dropdown:
        * Unlimited availability  -> service_seats = None
        * Limited seats          -> service_seats must be a number
    - For non-service products, this dropdown is ignored.
    """

    SERVICE_AVAILABILITY_CHOICES = [
        ("unlimited", "Unlimited availability"),
        ("limited", "Limited seats"),
    ]

    service_availability = forms.ChoiceField(
        choices=SERVICE_AVAILABILITY_CHOICES,
        required=False,
        label="Service availability",
        help_text="For service products: choose unlimited or limited seats.",
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance

        # Default: unlimited for services, ignored for others
        if instance and instance.pk and instance.is_service:
            if instance.service_seats is None:
                self.fields["service_availability"].initial = "unlimited"
            else:
                self.fields["service_availability"].initial = "limited"
        else:
            self.fields["service_availability"].initial = "unlimited"

        # Clarify how service_seats is used
        self.fields["service_seats"].help_text = (
            "Used only when availability is 'Limited seats'. "
            "Leave blank for unlimited availability."
        )

    def clean(self):
        cleaned_data = super().clean()

        is_service = cleaned_data.get("is_service")
        availability = cleaned_data.get("service_availability")
        seats = cleaned_data.get("service_seats")

        # Only apply special logic for service products
        if is_service:
            if availability == "unlimited":
                # Map dropdown -> service_seats = None
                cleaned_data["service_seats"] = None
            elif availability == "limited":
                if seats is None:
                    self.add_error(
                        "service_seats",
                        "Please enter the number of seats for a limited service.",
                    )

        return cleaned_data


class AccountEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = ("phone", "address1", "address2", "city", "province", "postal_code", "country")

