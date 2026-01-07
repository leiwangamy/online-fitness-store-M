from django import forms
import re

from .models import PickupLocation


class ShippingAddressForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        max_length=100,
        widget=forms.TextInput(attrs={
            "autocomplete": "given-name",
        }),
    )

    last_name = forms.CharField(
        label="Last name",
        max_length=100,
        widget=forms.TextInput(attrs={
            "autocomplete": "family-name",
        }),
    )

    phone = forms.CharField(
        label="Phone number",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel",
        }),
    )

    address1 = forms.CharField(
        label="Address line 1",
        max_length=255,
        widget=forms.TextInput(attrs={
            "autocomplete": "address-line1",
        }),
    )

    address2 = forms.CharField(
        label="Address line 2",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "address-line2",
        }),
    )

    city = forms.CharField(
        label="City",
        max_length=100,
        widget=forms.TextInput(attrs={
            "autocomplete": "address-level2",
        }),
    )

    province = forms.CharField(
        label="Province / State",
        max_length=100,
        widget=forms.TextInput(attrs={
            "autocomplete": "address-level1",
        }),
    )

    postal_code = forms.CharField(
        label="Postal code",
        max_length=20,
        widget=forms.TextInput(attrs={
            "autocomplete": "postal-code",
        }),
    )

    country = forms.CharField(
        label="Country",
        max_length=100,
        initial="Canada",
        widget=forms.TextInput(attrs={
            "autocomplete": "country",
            "readonly": True,
        }),
    )

    # Pickup option
    fulfillment_method = forms.ChoiceField(
        label="Fulfillment Method",
        choices=[
            ("shipping", "Ship to Address"),
            ("pickup", "Pick Up at Location"),
        ],
        initial="shipping",
        widget=forms.RadioSelect(attrs={
            "class": "fulfillment-method-radio",
        }),
    )
    
    pickup_location_id = forms.ModelChoiceField(
        queryset=PickupLocation.objects.none(),  # Will be set in __init__
        required=False,
        label="Pickup Location",
        empty_label="Select a pickup location",
        widget=forms.Select(attrs={
            "class": "pickup-location-select",
            "style": "display: none;",  # Hidden by default, shown when pickup is selected
        }),
    )
    
    def __init__(self, *args, **kwargs):
        # Extract pickup_locations if provided (for performance - avoid duplicate query)
        pickup_locations = kwargs.pop('pickup_locations', None)
        super().__init__(*args, **kwargs)
        # Update queryset to get current active pickup locations
        try:
            if pickup_locations is not None:
                # Ensure we have a queryset, not a list
                if hasattr(pickup_locations, 'filter'):
                    self.fields['pickup_location_id'].queryset = pickup_locations
                else:
                    # If it's a list, convert back to queryset
                    self.fields['pickup_location_id'].queryset = PickupLocation.objects.filter(is_active=True).order_by('display_order', 'name')
            else:
                self.fields['pickup_location_id'].queryset = PickupLocation.objects.filter(is_active=True).order_by('display_order', 'name')
        except (KeyError, AttributeError) as e:
            # If field doesn't exist or there's an error, use default queryset
            try:
                self.fields['pickup_location_id'].queryset = PickupLocation.objects.filter(is_active=True).order_by('display_order', 'name')
            except Exception:
                # If PickupLocation doesn't exist, use empty queryset
                self.fields['pickup_location_id'].queryset = PickupLocation.objects.none()

    # -------------------------
    # Validation
    # -------------------------
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if phone:
            cleaned = re.sub(r"[^\d+]", "", phone)
            if len(cleaned) < 7:
                raise forms.ValidationError("Enter a valid phone number.")
            return cleaned
        return phone

    def clean_postal_code(self):
        code = self.cleaned_data["postal_code"].strip().upper()

        # Canadian postal code: A1A 1A1
        if not re.match(r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$", code):
            raise forms.ValidationError("Enter a valid Canadian postal code.")

        return code
    
    def clean(self):
        cleaned_data = super().clean()
        fulfillment_method = cleaned_data.get("fulfillment_method")
        pickup_location_id = cleaned_data.get("pickup_location_id")
        
        # If pickup is selected, require pickup location
        if fulfillment_method == "pickup":
            if not pickup_location_id:
                raise forms.ValidationError({
                    "pickup_location_id": "Please select a pickup location."
                })
        
        # If shipping is selected, validate shipping address fields
        if fulfillment_method == "shipping":
            required_fields = ["first_name", "last_name", "address1", "city", "province", "postal_code"]
            for field in required_fields:
                if not cleaned_data.get(field):
                    if field not in self.errors:
                        self.add_error(field, "This field is required for shipping.")
        
        return cleaned_data
