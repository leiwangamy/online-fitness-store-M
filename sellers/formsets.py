"""
Formsets for managing multiple product media items (images, videos, audio)
Similar to admin inlines but for seller forms
"""
from django import forms
from django.forms import inlineformset_factory
from products.models import Product, ProductImage, ProductVideo, ProductAudio


class ProductImageForm(forms.ModelForm):
    """Form for a single product image"""
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'display_order', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Describe this image'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'image': 'Image File',
            'alt_text': 'Alt Text (Optional)',
            'display_order': 'Display Order',
            'is_main': 'Set as Main Image',
        }
        help_texts = {
            'image': 'Upload an image file (JPG, PNG, etc.)',
            'alt_text': 'Text description for accessibility',
            'display_order': 'Lower numbers appear first (0, 1, 2...)',
            'is_main': 'Only one image can be the main image',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field not required if this is a new form (no instance)
        if not self.instance.pk:
            self.fields['image'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # Skip validation if form is being deleted or is empty
        if self.cleaned_data.get('DELETE', False):
            return cleaned_data
        
        # If this is a new form (no instance) and no image is provided, skip validation
        if not self.instance.pk and not cleaned_data.get('image'):
            # Remove image from cleaned_data to avoid validation error
            if 'image' in cleaned_data:
                del cleaned_data['image']
        
        return cleaned_data


class ProductVideoForm(forms.ModelForm):
    """Form for a single product video"""
    class Meta:
        model = ProductVideo
        fields = ['title', 'video_file', 'video_url', 'display_order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Video title'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Or enter a video URL (YouTube, Vimeo, etc.)'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
        }
        labels = {
            'title': 'Video Title (Optional)',
            'video_file': 'Video File',
            'video_url': 'Or Video URL',
            'display_order': 'Display Order',
        }
        help_texts = {
            'title': 'Optional title for this video',
            'video_file': 'Upload a video file (MP4, MOV, etc.)',
            'video_url': 'Or provide a video URL instead',
            'display_order': 'Lower numbers appear first',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make video fields not required if this is a new form
        if not self.instance.pk:
            self.fields['video_file'].required = False
            self.fields['video_url'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # Skip validation if form is being deleted
        if self.cleaned_data.get('DELETE', False):
            return cleaned_data
        
        # If this is a new form and no video data is provided, skip validation
        if not self.instance.pk:
            video_file = cleaned_data.get('video_file')
            video_url = cleaned_data.get('video_url')
            if not video_file and not video_url:
                # Empty form - remove validation errors
                return cleaned_data
        
        # For existing forms or forms with data, validate normally
        video_file = cleaned_data.get('video_file')
        video_url = cleaned_data.get('video_url')
        # Only validate if we have an existing instance or if one of the fields is provided
        if self.instance.pk or video_file or video_url:
            if not video_file and not video_url:
                raise forms.ValidationError("Video must have either a video file or a video URL.")
        
        return cleaned_data


class ProductAudioForm(forms.ModelForm):
    """Form for a single product audio"""
    class Meta:
        model = ProductAudio
        fields = ['title', 'audio_file', 'audio_url', 'display_order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Audio title'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            }),
            'audio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Or enter an audio URL'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
        }
        labels = {
            'title': 'Audio Title (Optional)',
            'audio_file': 'Audio File',
            'audio_url': 'Or Audio URL',
            'display_order': 'Display Order',
        }
        help_texts = {
            'title': 'Optional title for this audio',
            'audio_file': 'Upload an audio file (MP3, WAV, etc.)',
            'audio_url': 'Or provide an audio URL instead',
            'display_order': 'Lower numbers appear first',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make audio fields not required if this is a new form
        if not self.instance.pk:
            self.fields['audio_file'].required = False
            self.fields['audio_url'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # Skip validation if form is being deleted
        if self.cleaned_data.get('DELETE', False):
            return cleaned_data
        
        # If this is a new form and no audio data is provided, skip validation
        if not self.instance.pk:
            audio_file = cleaned_data.get('audio_file')
            audio_url = cleaned_data.get('audio_url')
            if not audio_file and not audio_url:
                # Empty form - remove validation errors
                return cleaned_data
        
        # For existing forms or forms with data, validate normally
        audio_file = cleaned_data.get('audio_file')
        audio_url = cleaned_data.get('audio_url')
        # Only validate if we have an existing instance or if one of the fields is provided
        if self.instance.pk or audio_file or audio_url:
            if not audio_file and not audio_url:
                raise forms.ValidationError("Audio must have either an audio file or an audio URL.")
        
        return cleaned_data


# Create formsets
ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,  # Show 1 empty form by default
    can_delete=True,
    min_num=0,  # Allow products with no images
    validate_min=False,
    can_delete_extra=True,  # Allow deleting extra (empty) forms
)

ProductVideoFormSet = inlineformset_factory(
    Product,
    ProductVideo,
    form=ProductVideoForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    can_delete_extra=True,  # Allow deleting extra (empty) forms
)

ProductAudioFormSet = inlineformset_factory(
    Product,
    ProductAudio,
    form=ProductAudioForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    can_delete_extra=True,  # Allow deleting extra (empty) forms
)

