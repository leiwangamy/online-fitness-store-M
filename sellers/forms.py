"""
Forms for seller application and management
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from allauth.account.forms import SignupForm
from .models import Seller

User = get_user_model()


class SellerApplicationForm(forms.ModelForm):
    """
    Form for users to apply to become a seller.
    """
    class Meta:
        model = Seller
        fields = ['display_name', 'business_name', 'business_description']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your display name (e.g., "John\'s Fitness Store")'
            }),
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Your business name'
            }),
            'business_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Optional: Tell us about your business or what you plan to sell'
            }),
        }
        labels = {
            'display_name': 'Display Name',
            'business_name': 'Business Name (Optional)',
            'business_description': 'Business Description (Optional)',
        }
        help_texts = {
            'display_name': 'This name will be shown to customers on your products.',
            'business_name': 'If you have a registered business name.',
            'business_description': 'Brief description of your business or products.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['display_name'].required = True


class SellerSignupApplicationForm(SignupForm):
    """
    Combined form for new users to sign up and apply to become a seller in one step.
    Includes email, password, and seller application fields.
    """
    # Explicitly add email field (should be inherited from SignupForm, but making sure)
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    
    # Explicitly add password fields (should be inherited from SignupForm, but making sure)
    password1 = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        help_text='Your password must contain at least 8 characters.'
    )
    
    password2 = forms.CharField(
        required=True,
        label='Password (again)',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        help_text='Enter the same password as before, for verification.'
    )
    
    display_name = forms.CharField(
        max_length=120,
        required=True,
        label='Display Name',
        help_text='This name will be shown to customers on your products.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your display name (e.g., "John\'s Fitness Store")'
        })
    )
    business_name = forms.CharField(
        max_length=200,
        required=False,
        label='Business Name (Optional)',
        help_text='If you have a registered business name.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Your business name'
        })
    )
    business_description = forms.CharField(
        required=False,
        label='Business Description (Optional)',
        help_text='Brief description of your business or products.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Optional: Tell us about your business or what you plan to sell'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure email field exists and is styled
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Your email address'
            })
        # Ensure password fields exist and are styled
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Create a password'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Confirm your password'
            })
    
    def clean_password2(self):
        """Validate that both passwords match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2
    
    def save(self, request):
        """
        Create user account and seller application.
        """
        # Create the user account (handles email verification)
        user = super().save(request)
        
        # Create seller application
        seller = Seller.objects.create(
            user=user,
            display_name=self.cleaned_data['display_name'],
            business_name=self.cleaned_data.get('business_name', ''),
            business_description=self.cleaned_data.get('business_description', ''),
            status=Seller.STATUS_PENDING
        )
        
        return user


class SellerProductForm(forms.ModelForm):
    """
    Form for sellers to add/edit their products.
    Excludes seller field (auto-set), is_featured (admin-only), and adds media upload fields.
    """
    SERVICE_AVAILABILITY_CHOICES = (
        ("", "---------"),
        ("unlimited", "Unlimited seats"),
        ("limited", "Limited seats"),
    )
    
    service_availability = forms.ChoiceField(
        choices=SERVICE_AVAILABILITY_CHOICES,
        required=False,
        help_text="For service products only.",
    )
    
    class Meta:
        from products.models import Product
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'quantity_in_stock', 'is_active',
            'charge_gst', 'charge_pst',
            'is_digital', 'digital_file', 'digital_url',
            'is_service', 'service_seats',
            'service_date', 'service_time', 'service_duration_minutes', 'service_location'
        ]
        # Exclude: seller (auto-set), is_featured (admin-only)
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ensure is_featured is always False for seller products
        # This prevents any accidental setting of is_featured
        if hasattr(self, 'instance') and self.instance:
            self.instance.is_featured = False
        
        # Set initial service_availability based on instance
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if instance.is_service:
                self.fields['service_availability'].initial = (
                    "unlimited" if instance.service_seats is None else "limited"
                )
            else:
                self.fields['service_availability'].initial = ""
    
    def save(self, commit=True):
        """Override save to ensure is_featured is always False for seller products"""
        product = super().save(commit=False)
        product.is_featured = False  # Force is_featured to False
        if commit:
            product.save()
        return product
    
    def clean(self):
        cleaned = super().clean()
        
        is_service = bool(cleaned.get("is_service"))
        is_digital = bool(cleaned.get("is_digital"))
        
        digital_file = cleaned.get("digital_file")
        digital_url = cleaned.get("digital_url")
        
        availability = cleaned.get("service_availability")
        seats = cleaned.get("service_seats")
        
        # 1) type conflict
        if is_service and is_digital:
            raise forms.ValidationError("A product cannot be both digital and service.")
        
        # 2) digital requires file or url
        if is_digital and not (digital_file or digital_url):
            raise forms.ValidationError("Digital product must have a digital_file or digital_url.")
        
        # 3) service availability -> seats logic
        if is_service:
            if not availability:
                availability = "unlimited" if seats in (None, 0) else "limited"
            
            if availability == "unlimited":
                cleaned["service_seats"] = None
            elif availability == "limited":
                if seats in (None, 0):
                    raise forms.ValidationError("Limited seats service must have service_seats (>= 1).")
        else:
            # not service => clear service fields
            cleaned["service_seats"] = None
            cleaned["service_date"] = None
            cleaned["service_time"] = None
            cleaned["service_duration_minutes"] = None
            cleaned["service_location"] = ""
            cleaned["service_availability"] = ""
        
        return cleaned


class SellerProfileForm(forms.ModelForm):
    """
    Form for sellers to update their profile information.
    Allows updating display_name, business_name, business_description, and membership_intro_text.
    """
    class Meta:
        model = Seller
        fields = ['display_name', 'business_name', 'business_description', 'membership_intro_text']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your display name (e.g., "John\'s Fitness Store")'
            }),
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Your business name'
            }),
            'business_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Optional: Tell us about your business or what you sell'
            }),
            'membership_intro_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Introduction text shown at the top of your membership plans page'
            }),
        }
        labels = {
            'display_name': 'Display Name',
            'business_name': 'Business Name (Optional)',
            'business_description': 'Business Description (Optional)',
            'membership_intro_text': 'Membership Page Intro Text',
        }
        help_texts = {
            'display_name': 'This name will be shown to customers on your products and membership plans.',
            'business_name': 'If you have a registered business name.',
            'business_description': 'Brief description of your business or products.',
            'membership_intro_text': 'This text appears at the top of your public membership plans page.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['display_name'].required = True
