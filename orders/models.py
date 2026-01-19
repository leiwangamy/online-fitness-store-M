"""
Order Models Module

This module defines the order management system for the e-commerce platform.

Key Models:
- Order: Main order model containing customer information, totals, and fulfillment details
- OrderItem: Individual items within an order (product, quantity, price)
- PickupLocation: Physical locations where customers can pick up orders
- DigitalDownload: Secure download links for digital products with expiry

Order Lifecycle:
1. Order created with status "pending" or "paid" (depending on payment method)
2. Order items created for each product in cart
3. For digital products: DigitalDownload records created with secure links
4. For services: Service seats deducted from product availability
5. Order can be updated to "shipped", "delivered", "cancelled", etc.

Key Features:
- Support for shipping and pickup fulfillment methods
- Digital download link generation with expiry and download limits
- Order status tracking
- Tax and shipping calculation
- Order history for customers
- Admin panel integration for order management

Usage Example:
    # Create an order
    order = Order.objects.create(
        user=request.user,
        status="paid",
        subtotal=Decimal("100.00"),
        tax=Decimal("5.00"),
        shipping=Decimal("15.00"),
        total=Decimal("120.00"),
        is_pickup=False,
        ship_name="John Doe",
        ship_address1="123 Main St",
        ship_city="Toronto",
        ship_province="ON",
        ship_postal_code="M5H 2N2",
        ship_country="Canada"
    )
    
    # Add items to order
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price
    )
"""

import uuid
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product
from sellers.models import Seller


def default_expiry():
    """
    Default expiry for digital download links: 30 days from creation.
    
    Returns:
        datetime: Current time + 30 days
    """
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
    STATUS_REFUNDED = "refunded"
    STATUS_PARTIALLY_REFUNDED = "partially_refunded"
    STATUS_DISPUTED = "disputed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_PARTIALLY_REFUNDED, "Partially Refunded"),
        (STATUS_DISPUTED, "Disputed"),
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

    # Payment tracking (prevents double-charging)
    # Note: null=True allows existing orders, unique=True prevents duplicate payment intents
    # Empty strings are not unique, but actual payment_intent_ids must be unique
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        null=True,
        unique=True,
        help_text="Stripe payment intent ID or other payment gateway ID (unique to prevent double-charging)"
    )
    
    # Alias for payment_intent_id (for compatibility with refund code)
    @property
    def stripe_payment_intent_id(self):
        return self.payment_intent_id or ""

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
    
    seller = models.ForeignKey(
        Seller,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
        help_text="Seller who owns this product"
    )
    
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total for this line item (price * quantity)"
    )
    
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Platform commission fee"
    )
    
    seller_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount seller earns after commission"
    )

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return (self.price or Decimal("0.00")) * self.quantity
    
    def save(self, *args, **kwargs):
        """
        Automatically calculate seller, line_total, platform_fee, and seller_earnings
        when saving OrderItem.
        """
        # Set seller from product
        if self.product and self.product.seller:
            self.seller = self.product.seller
        
        # Calculate line_total (unit_price * quantity)
        unit_price = self.price or Decimal("0.00")
        qty = self.quantity or 0
        self.line_total = unit_price * qty
        
        # Calculate commission if seller exists
        if self.seller and self.line_total > Decimal("0.00"):
            # Platform fee = line_total * commission_rate
            self.platform_fee = self.line_total * self.seller.commission_rate
            # Seller earnings = line_total - platform_fee
            self.seller_earnings = self.line_total - self.platform_fee
        else:
            # No seller or zero total - no commission
            self.platform_fee = Decimal("0.00")
            self.seller_earnings = self.line_total  # Seller gets full amount if no commission
        
        super().save(*args, **kwargs)


class Refund(models.Model):
    """
    Refund model for tracking order refunds.
    
    Status flow:
    - requested: Seller or customer requested refund, awaiting admin approval
    - approved: Admin approved, ready to process
    - rejected: Admin rejected the refund request
    - processing: Refund is being processed (Stripe call in progress)
    - succeeded: Refund completed successfully
    - failed: Refund processing failed
    """
    STATUS_REQUESTED = "requested"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PROCESSING = "processing"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    
    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="refunds",
        help_text="Order being refunded"
    )
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.PROTECT,
        related_name="refunds",
        help_text="Seller who owns the product being refunded"
    )
    order_item = models.ForeignKey(
        'OrderItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="refunds",
        help_text="Specific order item being refunded (null for full order refunds)"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Refund amount (in CAD)"
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for refund"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="refunds_created",
        help_text="User who initiated the refund"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED,
        help_text="Current refund status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stripe refund ID
    stripe_refund_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe refund ID after processing"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
    
    def __str__(self):
        return f"Refund #{self.id} - Order #{self.order.id} - ${self.amount} ({self.get_status_display()})"


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
    
    


