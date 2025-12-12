from django.db import models
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from datetime import timedelta


# =========================
#  CATEGORY
# =========================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# =========================
#  PRODUCT
# =========================
class Product(models.Model):
    # Product belongs to one category (optional)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    # Stock quantity (for physical products, or simple service stock)
    quantity_in_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Available quantity",
    )

    # Tax flags
    charge_gst = models.BooleanField(default=True, verbose_name="Charge GST (5%)")
    charge_pst = models.BooleanField(default=False, verbose_name="Charge PST (7%)")

    # PRODUCT TYPE FLAGS
    is_digital = models.BooleanField(default=False)   # Instant download product
    is_service = models.BooleanField(default=False)   # Yoga class, coaching, etc.

    # SERVICE-ONLY FIELDS
    # Seats: if set -> limited seats; if blank -> unlimited seats
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

    # ----- Tax helper properties -----
    @property
    def gst_amount(self):
        return (
            self.price
            * Decimal("0.05")
            * (1 if self.charge_gst else 0)
        ).quantize(Decimal("0.01"))

    @property
    def pst_amount(self):
        return (
            self.price
            * Decimal("0.07")
            * (1 if self.charge_pst else 0)
        ).quantize(Decimal("0.01"))

    @property
    def price_with_tax(self):
        total = self.price + self.gst_amount + self.pst_amount
        return total.quantize(Decimal("0.01"))

    # ----- Helper: type checks -----
    @property
    def is_physical(self):
        """Convenience flag: physical = not digital and not service."""
        return not self.is_digital and not self.is_service

    # ----- Helper: availability text for templates -----
    @property
    def availability_text(self):
        """
        Human-friendly availability info to show on product pages.
        - Digital: 'Instant download'
        - Service: 'X seats left' / 'Unlimited seats' / 'Fully booked'
        - Physical: 'In stock: N' / 'Out of stock'
        """
        if self.is_digital:
            return "Instant download"

        if self.is_service:
            if self.service_seats is None:
                return "Unlimited seats"
            if self.service_seats > 0:
                return f"{self.service_seats} seats left"
            return "Fully booked"

        # Physical product
        if self.quantity_in_stock > 0:
            return f"In stock: {self.quantity_in_stock}"
        return "Out of stock"

    # ⭐ MAIN IMAGE HELPERS
    @property
    def main_image(self):
        """Return main image if exists, else first image, else None."""
        # 1. Try main image
        main = self.images.filter(is_main=True).first()
        if main:
            return main.image.url

        # 2. Fallback to first uploaded
        first = self.images.first()
        if first:
            return first.image.url

        # 3. Nothing found
        return None

    def __str__(self):
        return self.name


# =========================
#  PRODUCT MEDIA
# =========================
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    # ⭐ Which image is the main one on the card
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
            # Ensure only one main image per product
            ProductImage.objects.filter(
                product=self.product,
                is_main=True,
            ).exclude(id=self.id).update(is_main=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="videos",
    )
    title = models.CharField(max_length=200, blank=True)
    video_file = models.FileField(
        upload_to="product_videos/",
        blank=True,
        null=True,
    )
    video_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Video {self.title or self.id}"


class ProductAudio(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="audios",
    )
    title = models.CharField(max_length=200, blank=True)
    audio_file = models.FileField(
        upload_to="product_audio/",
        blank=True,
        null=True,
    )
    audio_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Audio {self.title or self.id}"


# =========================
#  MEMBER PROFILE / MEMBERSHIP
# =========================
class MemberProfile(models.Model):
    MEMBERSHIP_LEVEL_CHOICES = [
        ("none", "No membership"),
        ("basic", "Facility only – unlimited gym access"),
        ("premium", "Facility + unlimited in-class training"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )

    membership_level = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_LEVEL_CHOICES,
        default="none",
    )

    is_member = models.BooleanField(default=False)
    membership_started = models.DateTimeField(blank=True, null=True)
    membership_expires = models.DateTimeField(blank=True, null=True)

    # Auto-billing description fields (no real payment yet)
    auto_renew = models.BooleanField(
        default=False,
        help_text="If enabled, membership will auto-renew each month (logic only, no real billing).",
    )

    next_billing_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of next renewal charge (for display / logic only).",
    )

    last_billed_date = models.DateField(
        blank=True,
        null=True,
        help_text="Most recent date membership was 'renewed'.",
    )

    def __str__(self):
        return f"{self.user.username} – {self.get_membership_level_display()}"

    @property
    def is_active_member(self):
        """
        Active if:
        - is_member is True
        - and not expired (or no expiry set)
        """
        if not self.is_member:
            return False
        if self.membership_expires and self.membership_expires < timezone.now():
            return False
        return True

    # ------- Helper methods to show auto-billing logic (no real billing) -------

    def start_monthly_membership(self, level, price=None):
        """
        Example logic of how monthly membership could be started.
        This does NOT charge any money, it's just for your internal logic.
        """
        now = timezone.now()

        self.membership_level = level          # "basic" or "premium"
        self.is_member = True
        self.membership_started = now

        # ✅ membership period
        expiry = now + timedelta(days=30)
        self.membership_expires = expiry

        self.auto_renew = True

        # ✅ billing happens AFTER expiry (next day)
        self.next_billing_date = (expiry + timedelta(days=1)).date()

        self.last_billed_date = now.date()
        self.save()


    def simulate_monthly_billing_cycle(self):
        """
        Pseudo-code of an auto-billing cycle.

        If today >= next_billing_date and auto_renew is True:
            - In real life: charge credit card (Stripe/PayPal/etc.)
            - If success: extend membership_expires + move next_billing_date
            - If fail: set is_member = False and auto_renew = False

        Here we only update dates to demonstrate the logic.
        """
        today = timezone.now().date()
        if not self.auto_renew or not self.is_member:
            return

        if self.next_billing_date and today >= self.next_billing_date:
            # In a real system, you would attempt a payment here.

            # Simulate success: extend another 30 days
            now = timezone.now()
            self.membership_expires = now + timedelta(days=30)
            self.last_billed_date = today
            self.next_billing_date = today + timedelta(days=30)
            self.save()


# ---------- signals to auto-create MemberProfile ----------
User = get_user_model()


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    if created:
        MemberProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_member_profile(sender, instance, **kwargs):
    if hasattr(instance, "member_profile"):
        instance.member_profile.save()


# =========================
#  ORDER + ORDER ITEM
# =========================
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    CARRIER_CHOICES = [
        ("canadapost", "Canada Post"),
        ("ups", "UPS"),
        ("fedex", "FedEx"),
        ("dhl", "DHL"),
        ("other", "Other / Local"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Shipping tracking number (if applicable)",
    )

    shipping_carrier = models.CharField(
        max_length=20,
        choices=CARRIER_CHOICES,
        blank=True,
        null=True,
        help_text="Shipping company for physical items",
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    shipping = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order #{self.pk} ({self.user})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit at time of purchase",
    )

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
