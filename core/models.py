from django.db import models
from django.utils import timezone


class CompanyInfo(models.Model):
    """
    Stores company contact information that can be edited by admin
    and displayed to users on the contact page.
    """
    phone = models.CharField(max_length=20, default="778-238-3371")
    email = models.EmailField(default="info@lwsoc.com")
    address = models.TextField(
        blank=True,
        help_text="Company address or description"
    )
    description = models.TextField(
        blank=True,
        help_text="Additional information about the company"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Information"
        verbose_name_plural = "Company Information"
    
    def __str__(self):
        return f"Company Info (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the single instance of CompanyInfo"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class UserDeletion(models.Model):
    """
    Tracks soft-deleted users with a 30-day recovery window.
    """
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='deletion_record'
    )
    deleted_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, help_text="Optional reason for deletion")
    
    class Meta:
        verbose_name = "User Deletion"
        verbose_name_plural = "User Deletions"
        ordering = ['-deleted_at']
    
    def __str__(self):
        return f"Deletion: {self.user.email} ({self.deleted_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def days_until_permanent(self):
        """Calculate days remaining until permanent deletion"""
        days_since = (timezone.now() - self.deleted_at).days
        return max(0, 30 - days_since)
    
    @property
    def can_recover(self):
        """Check if account can still be recovered (within 30 days)"""
        return self.days_until_permanent > 0
    
    @property
    def is_permanent(self):
        """Check if deletion is now permanent (past 30 days)"""
        return not self.can_recover
