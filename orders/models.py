# orders/models.py

import uuid
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


def default_expiry():
    # default download link expiry: 30 days
    return timezone.now() + timedelta(days=30)


class PickupLocation(models.Model):
    """Pickup locations that customers can select during checkout."""
    name = models.CharField(max_length=200, help_text="Location name (e.g., 'Main Store', 'Downtown Branch')")
    address1 = models.CharField(max_length=255, help_text="Street address")
    address2 = models.CharField(max_length=255, blank=True, default="", help_text="Apartment, suite, etc. (optional)")
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Canada")
    phone = models.CharField(max_length=30, blank=True, default="", help_text="Contact phone for this location")
    instructions = models.TextField(blank=True, default="", help_text="Special instructions for customers (e.g., 'Pick up at front desk', 'Hours: Mon-Fri 9am-5pm')")
    is_active = models.BooleanField(default=True, help_text="Only active locations are shown to customers")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which locations appear (lower numbers first)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Pickup Location"
        verbose_name_plural = "Pickup Locations"
    
    def __str__(self):
        return self.name
    
    def full_address(self) -> str:
        """Return formatted full address."""
        lines = []
        if self.address1:
            lines.append(self.address1)
        if self.address2:
            lines.append(self.address2)
        city_line = " ".join([p for p in [self.city, self.province, self.postal_code] if p]).strip()
        if city_line:
            lines.append(city_line)
        if self.country:
            lines.append(self.country)
        return "\n".join(lines)


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    CARRIER_CANADAPOST = "canadapost"
    CARRIER_UPS = "ups"
    CARRIER_FEDEX = "fedex"
    CARRIER_DHL = "dhl"
    CARRIER_OTHER = "other"

    CARRIER_CHOICES = [
        (CARRIER_CANADAPOST, "Canada Post"),
        (CARRIER_UPS, "UPS"),
        (CARRIER_FEDEX, "FedEx"),
        (CARRIER_DHL, "DHL"),
        (CARRIER_OTHER, "Other / Local"),
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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    tracking_number = models.CharField(max_length=100, blank=True, default="")
    shipping_carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES, blank=True, default="")

    # Pickup option
    is_pickup = models.BooleanField(default=False, help_text="If True, customer selected pickup instead of shipping")
    pickup_location = models.ForeignKey(
        'PickupLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Selected pickup location (only set if is_pickup=True)"
    )

    # Shipping address snapshot (store on the order)
    ship_name = models.CharField(max_length=200, blank=True, default="")
    ship_phone = models.CharField(max_length=30, blank=True, default="")
    ship_address1 = models.CharField(max_length=255, blank=True, default="")
    ship_address2 = models.CharField(max_length=255, blank=True, default="")
    ship_city = models.CharField(max_length=100, blank=True, default="")
    ship_province = models.CharField(max_length=100, blank=True, default="")
    ship_postal_code = models.CharField(max_length=20, blank=True, default="")
    ship_country = models.CharField(max_length=100, blank=True, default="")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"Order #{self.pk} ({self.user})"

    def shipping_full(self) -> str:
        """Return shipping address or pickup location address."""
        if self.is_pickup and self.pickup_location:
            return f"PICKUP: {self.pickup_location.name}\n{self.pickup_location.full_address()}"
        
        lines = []
        if self.ship_name:
            lines.append(self.ship_name)
        if self.ship_phone:
            lines.append(self.ship_phone)
        if self.ship_address1:
            lines.append(self.ship_address1)
        if self.ship_address2:
            lines.append(self.ship_address2)

        city_line = " ".join(
            [p for p in [self.ship_city, self.ship_province, self.ship_postal_code] if p]
        ).strip()
        if city_line:
            lines.append(city_line)

        if self.ship_country:
            lines.append(self.ship_country)

        return "\n".join(lines)

    shipping_full.short_description = "Shipping/Pickup Address"  # admin label

    def lock_shipping_if_fulfillment_started(self) -> bool:
        """
        If order is already paid/shipped/delivered, we usually don't want
        shipping address changed by accident.
        """
        return self.status in {self.STATUS_PAID, self.STATUS_SHIPPED, self.STATUS_DELIVERED}

    def save(self, *args, **kwargs):
        if self.pk and self.lock_shipping_if_fulfillment_started():
            old = Order.objects.filter(pk=self.pk).first()
            if old:
                # keep the original shipping snapshot
                self.ship_name = old.ship_name
                self.ship_phone = old.ship_phone
                self.ship_address1 = old.ship_address1
                self.ship_address2 = old.ship_address2
                self.ship_city = old.ship_city
                self.ship_province = old.ship_province
                self.ship_postal_code = old.ship_postal_code
                self.ship_country = old.ship_country

        super().save(*args, **kwargs)

    @property
    def items_total(self) -> Decimal:
        """
        Total from items (price * qty). Useful if you want to recompute totals.
        """
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unit price at time of purchase"
    )

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return (self.price or Decimal("0.00")) * self.quantity


class DigitalDownload(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="downloads")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="downloads")

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(default=default_expiry)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="uniq_order_product_download"
            )
        ]

    # Set to a very large number if you want "unlimited"
    max_downloads = models.PositiveIntegerField(default=3)
    download_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Download {self.product} ({self.order_id})"

    def is_valid(self) -> bool:
        if timezone.now() > self.expires_at:
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True

    @classmethod
    def create_default(cls, order, product, days=30, max_downloads=3):
        """
        Create (or reuse) a digital download link.
        """
        obj, _ = cls.objects.get_or_create(
            order=order,
            product=product,
            defaults={
                "expires_at": timezone.now() + timedelta(days=days),
                "max_downloads": max_downloads,
            },
        )
        return obj
    
    


