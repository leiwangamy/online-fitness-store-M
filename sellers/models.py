# sellers/models.py
from django.conf import settings
from django.db import models
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
