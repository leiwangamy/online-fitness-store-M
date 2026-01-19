"""
Product Models Module

This module defines the core product models for the e-commerce platform:
- Category: Product categories for organization
- Product: Main product model supporting physical, digital, and service products
- ProductImage: Product image management with main image support

Key Features:
- Support for three product types: physical, digital, and service
- Inventory management for physical products
- Digital file/URL support for digital products
- Service booking with seat management
- Tax calculation (GST/PST)
- Product image management with main image selection
"""

from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError

from django.conf import settings
from sellers.models import Seller

# =========================
#  CATEGORY
# =========================
class Category(models.Model):
    """
    Product Category Model
    
    Organizes products into categories. Each product can belong to one category.
    Categories are used for filtering and organizing products on the storefront.
    
    Attributes:
        name: Category name (unique)
        slug: URL-friendly identifier (unique, auto-generated from name)
    
    Example:
        Category: "Yoga Equipment", "Digital Downloads", "Fitness Classes"
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# =========================
#  PRODUCT
# =========================
class Product(models.Model):
    """
    Product Model - Core E-commerce Product
    
    Supports three product types:
    1. Physical Products: Require shipping, have inventory
    2. Digital Products: Instant download, file or URL-based
    3. Service Products: Bookable services with seat management
    
    Key Features:
    - Flexible product type system (physical/digital/service)
    - Inventory tracking for physical products
    - Digital file/URL delivery for digital products
    - Service booking with date/time/location
    - Tax calculation (GST/PST flags)
    - Product images with main image selection
    - Active/inactive status for product management
    
    Validation Rules:
    - Cannot be both digital and service
    - Digital products must have file or URL
    - Service products should have quantity_in_stock = 0
    
    Usage Example:
        # Create a physical product
        product = Product.objects.create(
            name="Yoga Mat",
            price=29.99,
            quantity_in_stock=50,
            is_digital=False,
            is_service=False
        )
        
        # Create a digital product
        digital = Product.objects.create(
            name="Yoga Video",
            price=9.99,
            is_digital=True,
            digital_file=uploaded_file
        )
        
        # Create a service product
        service = Product.objects.create(
            name="Yoga Class",
            price=25.00,
            is_service=True,
            service_seats=20,
            service_date=date(2024, 1, 15),
            service_time=time(18, 0)
        )
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    
    seller = models.ForeignKey(
        Seller,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        help_text="Seller who owns this product"
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Featured products appear on the home page")

    # Physical stock
    quantity_in_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Available quantity",
    )

    # Tax flags (adjust rates in your checkout logic, not here)
    charge_gst = models.BooleanField(default=True, verbose_name="Charge GST (5%)")
    charge_pst = models.BooleanField(default=False, verbose_name="Charge PST (7%)")

    # Type flags
    is_digital = models.BooleanField(default=False)
    is_service = models.BooleanField(default=False)

    # Digital fields (file OR url)
    digital_file = models.FileField(upload_to="digital_products/", blank=True, null=True)
    digital_url = models.URLField(blank=True, null=True)

    # Service-only fields
    service_seats = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of seats. Leave blank for unlimited.",
    )
    service_date = models.DateField(blank=True, null=True)
    service_time = models.TimeField(blank=True, null=True)
    service_duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Length of class in minutes",
    )
    service_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. Studio Room A, Zoom link, park location",
    )

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    # -------------------------
    # Validation / sanity rules
    # -------------------------
    def clean(self):
        super().clean()

        # Prevent impossible types: digital + service at same time
        if self.is_digital and self.is_service:
            raise ValidationError("A product cannot be both digital and service.")

        # Digital must have file or url
        if self.is_digital and not (self.digital_file or self.digital_url):
            raise ValidationError("Digital products must have a digital file or a digital URL.")

        # Non-digital shouldn't keep digital fields (optional strictness)
        # If you don't want this, remove these two checks.
        if not self.is_digital and (self.digital_file or self.digital_url):
            raise ValidationError("Non-digital products should not have digital_file/digital_url.")

        # Service products generally shouldn't have physical stock
        if self.is_service and self.quantity_in_stock != 0:
            raise ValidationError("Service products should have quantity_in_stock = 0 (use service_seats instead).")

    # -------------------------
    # Tax helper properties
    # -------------------------
    @property
    def gst_amount(self):
        rate = Decimal("0.05")
        return (self.price * rate if self.charge_gst else Decimal("0.00")).quantize(Decimal("0.01"))

    @property
    def pst_amount(self):
        rate = Decimal("0.07")
        return (self.price * rate if self.charge_pst else Decimal("0.00")).quantize(Decimal("0.01"))

    @property
    def price_with_tax(self):
        return (self.price + self.gst_amount + self.pst_amount).quantize(Decimal("0.01"))

    # -------------------------
    # Convenience helpers
    # -------------------------
    @property
    def is_physical(self):
        return (not self.is_digital) and (not self.is_service)

    @property
    def availability_text(self):
        if self.is_digital:
            return "Instant download"

        if self.is_service:
            if self.service_seats is None:
                return "Unlimited seats"
            if self.service_seats > 0:
                return f"{self.service_seats} seats left"
            return "Fully booked"

        # Physical
        return f"In stock: {self.quantity_in_stock}" if self.quantity_in_stock > 0 else "Out of stock"

    @property
    def main_image_url(self):
        """
        Returns URL of main image if set, else first image URL, else None.
        Safe for templates: {{ product.main_image_url }}
        Works efficiently with prefetched images.
        """
        try:
            # Check if images are prefetched by accessing the cached queryset
            # If prefetched, use the cached data; otherwise query the DB
            if hasattr(self, '_prefetched_objects_cache') and 'images' in self._prefetched_objects_cache:
                images = self._prefetched_objects_cache['images']
            else:
                images = list(self.images.all())
            
            # Look for main image first
            for img in images:
                if img.is_main and img.image and img.image.name:
                    return img.image.url
            
            # If no main image, return first image
            for img in images:
                if img.image and img.image.name:
                    return img.image.url
        except Exception:
            # If anything goes wrong, return None (template will handle fallback)
            pass
        
        return None

    def __str__(self) -> str:
        return self.name


# =========================
#  PRODUCT MEDIA
# =========================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order", "id"]
        indexes = [
            models.Index(fields=["product", "display_order"]),
            models.Index(fields=["product", "is_main"]),
        ]

    def save(self, *args, **kwargs):
        # Ensure only one main image per product
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product.name} - Image {self.id}"


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=200, blank=True)
    video_file = models.FileField(upload_to="product_videos/", blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def clean(self):
        super().clean()
        if not (self.video_file or self.video_url):
            raise ValidationError("Video must have a video_file or a video_url.")

    def __str__(self) -> str:
        return f"{self.product.name} - Video {self.title or self.id}"


class ProductAudio(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="audios")
    title = models.CharField(max_length=200, blank=True)
    audio_file = models.FileField(upload_to="product_audio/", blank=True, null=True)
    audio_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def clean(self):
        super().clean()
        if not (self.audio_file or self.audio_url):
            raise ValidationError("Audio must have an audio_file or an audio_url.")

    def __str__(self) -> str:
        return f"{self.product.name} - Audio {self.title or self.id}"


class InventoryLog(models.Model):
    
    class ChangeType(models.TextChoices):
        INITIAL = "INITIAL", "Beginning balance"
        ORDER = "ORDER", "Order"
        RESTOCK = "RESTOCK", "Restock"
        ADJUST = "ADJUST", "Manual adjustment"
        REFUND = "REFUND", "Refund/Return"

    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="inventory_logs")
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    delta = models.IntegerField()  # negative = reduce, positive = add
    note = models.CharField(max_length=255, blank=True)
    order_id = models.IntegerField(null=True, blank=True)  # simple link to order without circular imports
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} {self.delta} ({self.change_type})"