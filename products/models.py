from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError

from django.conf import settings

# =========================
#  CATEGORY
# =========================
class Category(models.Model):
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
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)

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
        """
        main = self.images.filter(is_main=True).first()
        if main and main.image:
            return main.image.url
        first = self.images.first()
        if first and first.image:
            return first.image.url
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