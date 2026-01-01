from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class MemberProfile(models.Model):
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

    membership_level = models.CharField(max_length=20, choices=MEMBERSHIP_LEVEL_CHOICES, default="none")
    is_member = models.BooleanField(default=False)
    membership_started = models.DateTimeField(blank=True, null=True)
    membership_expires = models.DateTimeField(blank=True, null=True)

    auto_renew = models.BooleanField(default=False)
    next_billing_date = models.DateField(blank=True, null=True)
    last_billed_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} – {self.get_membership_level_display()}"

    @property
    def is_active_member(self) -> bool:
        if not self.is_member:
            return False
        return not (self.membership_expires and self.membership_expires < timezone.now())

    def start_monthly_membership(self, level: str):
        now = timezone.now()
        expiry = now + timedelta(days=30)

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
