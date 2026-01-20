from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class MemberProfile(models.Model):
    # Legacy choices kept for reference, but field no longer uses choices constraint
    MEMBERSHIP_LEVEL_CHOICES = [
        ("none", "No membership"),
        ("basic", "Facility only – unlimited gym access"),
        ("premium", "Facility + unlimited in-class training"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership",  # ✅ IMPORTANT: avoid conflict with profiles.Profile related_name="profile"
    )

    # Single membership field - user can have EITHER platform OR seller membership (not both)
    membership_level = models.CharField(max_length=100, default="none", help_text="Membership plan identifier (slug). Can be a platform plan slug or seller plan full slug (seller_X_slug)")
    is_member = models.BooleanField(default=False)
    membership_started = models.DateTimeField(blank=True, null=True)
    membership_expires = models.DateTimeField(blank=True, null=True)
    auto_renew = models.BooleanField(default=False)
    next_billing_date = models.DateField(blank=True, null=True)
    last_billed_date = models.DateField(blank=True, null=True)

    def __str__(self):
        level_display = self.get_membership_level_display()
        if level_display == self.membership_level:
            # If display is same as value, it means it's not in choices (likely a seller plan)
            # Try to get a better display name
            if self.membership_level.startswith("seller_"):
                try:
                    from sellers.models import SellerMembershipPlan
                    parts = self.membership_level.split('_', 2)
                    if len(parts) == 3:
                        seller_id = parts[1]
                        slug = parts[2]
                        plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
                        level_display = f"{plan.seller.display_name or plan.seller.user.username} - {plan.name}"
                except Exception:
                    pass
        return f"{self.user} – {level_display}"

    @property
    def is_active_member(self) -> bool:
        """Check if user has an active membership"""
        if not self.is_member:
            return False
        return not (self.membership_expires and self.membership_expires < timezone.now())

    def start_monthly_membership(self, level: str, plan_type: str = "auto"):
        """
        Start a monthly membership. Replaces any existing membership.
        If plan_type is 'auto', it will be determined from the level.
        plan_type can be 'platform', 'seller', or 'auto'
        """
        now = timezone.now()
        expiry = now + timedelta(days=30)

        # Set the membership (replaces any existing one)
        self.membership_level = level
        self.is_member = True
        self.membership_started = now
        self.membership_expires = expiry
        self.auto_renew = True
        self.last_billed_date = now.date()
        self.next_billing_date = (expiry + timedelta(days=1)).date()
        
        self.save()

    def simulate_monthly_billing_cycle(self):
        today = timezone.now().date()
        if not (self.auto_renew and self.is_member and self.next_billing_date):
            return
        if today >= self.next_billing_date:
            now = timezone.now()
            self.membership_expires = now + timedelta(days=30)
            self.last_billed_date = today
            self.next_billing_date = today + timedelta(days=30)
            self.save()

# Note: Member profile creation signal is in signals.py to avoid duplicates


class MembershipPlan(models.Model):
    """
    Flexible membership plan model - similar to PickupLocation.
    Allows admins to add/remove membership plan types dynamically.
    """
    name = models.CharField(
        max_length=200,
        help_text="Plan name (e.g., 'Basic', 'Premium', 'VIP')"
    )
    slug = models.SlugField(
        unique=True,
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
        verbose_name = "Membership Plan"
        verbose_name_plural = "Membership Plans"
    
    def __str__(self):
        return self.name
    
    @property
    def price_display(self):
        """Return formatted price string"""
        return f"${self.price} / month"
    
    def has_active_members(self):
        """Check if this plan has any active member subscriptions"""
        active_count = MemberProfile.objects.filter(
            membership_level=self.slug,
            is_member=True
        ).exclude(
            membership_expires__lt=timezone.now()
        ).count()
        return active_count > 0
    
    def get_active_member_count(self):
        """Get the number of active members subscribed to this plan"""
        return MemberProfile.objects.filter(
            membership_level=self.slug,
            is_member=True
        ).exclude(
            membership_expires__lt=timezone.now()
        ).count()
    
    # Note: Deletion protection is handled at the admin level (members/admin.py)
    # The admin's delete_model/delete_queryset methods prevent deletion and show friendly messages
    # The model's delete() method is allowed to proceed normally since admin handles the check
