# sellers/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Seller(models.Model):
    """
    Seller model representing users who can sell products on the platform.
    
    Status flow:
    - PENDING: User has applied, waiting for admin approval
    - APPROVED: Admin approved, seller can now add products
    - REJECTED: Admin rejected the application
    """
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller"
    )
    display_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Seller application status"
    )
    
    # Commission used later for payments
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.10"),
        help_text="Platform commission rate (e.g., 0.10 = 10%)"
    )
    
    # Payout settings
    payout_hold_days = models.PositiveIntegerField(
        default=7,
        help_text="Number of days to hold earnings before they become available for payout (default: 7 days)"
    )
    
    # Optional business information
    business_name = models.CharField(max_length=200, blank=True, help_text="Optional business name")
    business_description = models.TextField(blank=True, help_text="Optional business description")
    
    # Membership page intro text
    membership_intro_text = models.TextField(
        blank=True,
        default="Choose a seller membership plan that fits your needs.",
        help_text="Introduction text shown at the top of your membership plans page"
    )
    
    # Stripe Connect account (for future payment processing)
    stripe_account_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe Connect account ID"
    )
    
    # Trust/risk tier (for future auto-refund permissions)
    is_trusted = models.BooleanField(
        default=False,
        help_text="Trusted sellers may have additional permissions (e.g., auto-refund)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Seller"
        verbose_name_plural = "Sellers"
        ordering = ['-created_at']

    def __str__(self):
        return self.display_name or self.user.get_username()
    
    @property
    def is_approved(self):
        """Backward compatibility: check if status is APPROVED"""
        return self.status == self.STATUS_APPROVED
    
    @property
    def is_pending(self):
        """Check if application is pending"""
        return self.status == self.STATUS_PENDING
    
    @property
    def is_rejected(self):
        """Check if application was rejected"""
        return self.status == self.STATUS_REJECTED


class SellerMembershipPlan(models.Model):
    """
    Membership plans created by sellers.
    Similar to admin MembershipPlan but owned by a seller.
    """
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name="membership_plans",
        help_text="Seller who owns this membership plan"
    )
    name = models.CharField(
        max_length=200,
        help_text="Plan name (e.g., 'Basic', 'Premium', 'VIP')"
    )
    slug = models.SlugField(
        help_text="URL-friendly identifier (e.g., 'basic', 'premium', 'vip')"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monthly price (use 0.00 for free plans)"
    )
    description = models.TextField(
        help_text="Brief description. HTML supported: &lt;p&gt;, &lt;ul&gt;, &lt;li&gt;, &lt;strong&gt;, etc."
    )
    details = models.TextField(
        blank=True,
        default="",
        help_text="Additional details (optional). HTML supported: &lt;ul&gt;&lt;li&gt; for lists, &lt;p&gt; for paragraphs."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active plans are shown to customers"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which plans appear (lower numbers first)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Seller Membership Plan"
        verbose_name_plural = "Seller Membership Plans"
        unique_together = [['seller', 'slug']]  # Slug must be unique per seller
    
    def __str__(self):
        return f"{self.seller.display_name or self.seller.user.username} - {self.name}"
    
    @property
    def price_display(self):
        """Return formatted price string"""
        return f"${self.price} / month"
    
    def has_active_members(self):
        """Check if this plan has any active member subscriptions"""
        from members.models import MemberProfile
        active_count = MemberProfile.objects.filter(
            membership_level=self.get_full_slug(),
            is_member=True
        ).exclude(
            membership_expires__lt=timezone.now()
        ).count()
        return active_count > 0
    
    def get_active_member_count(self):
        """Get the number of active members subscribed to this plan"""
        from members.models import MemberProfile
        return MemberProfile.objects.filter(
            membership_level=self.get_full_slug(),
            is_member=True
        ).exclude(
            membership_expires__lt=timezone.now()
        ).count()
    
    def get_full_slug(self):
        """Get the full slug that includes seller identifier for uniqueness"""
        return f"seller_{self.seller.id}_{self.slug}"
