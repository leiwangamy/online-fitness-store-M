from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator


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


class BlogPost(models.Model):
    """
    Blog post model for content management.
    Allows admins to create and manage blog posts through the admin panel.
    """
    title = models.CharField(
        max_length=200,
        help_text="Title of the blog post"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly version of the title (e.g., 'my-first-post')"
    )
    author = models.CharField(
        max_length=100,
        default="Fitness Club",
        help_text="Author name"
    )
    content = models.TextField(
        help_text="Main content of the blog post. You can use HTML formatting."
    )
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short summary/excerpt (optional, up to 500 characters)"
    )
    featured_image = models.ImageField(
        upload_to='blog_images/',
        blank=True,
        null=True,
        help_text="Featured image for the blog post (optional)"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Check to publish this post. Unpublished posts won't be visible to visitors."
    )
    published_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Publication date. Leave blank to use current date when published."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-set published_date when first published
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('core:blog_detail', kwargs={'slug': self.slug})


class BlogPostImage(models.Model):
    """
    Multiple images for a blog post.
    Allows admins to add multiple images to a single blog post.
    """
    blog_post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(
        upload_to='blog_images/',
        help_text="Image file"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility (optional)"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which images are displayed (lower numbers first)"
    )
    is_main = models.BooleanField(
        default=False,
        help_text="Mark this as the main/featured image"
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "Blog Post Image"
        verbose_name_plural = "Blog Post Images"
        indexes = [
            models.Index(fields=['blog_post', 'display_order']),
            models.Index(fields=['blog_post', 'is_main']),
        ]

    def save(self, *args, **kwargs):
        # Ensure only one main image per blog post
        if self.is_main:
            BlogPostImage.objects.filter(
                blog_post=self.blog_post,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.blog_post.title} - Image {self.id}"


class MembershipPlanContent(models.Model):
    """
    Content model for membership plans page header/intro only.
    Actual plans are managed through MembershipPlan model (in members app).
    Singleton pattern - only one instance should exist.
    """
    # Page header/intro
    page_title = models.CharField(
        max_length=200,
        default="Membership Plans",
        help_text="Main title shown on the membership page"
    )
    intro_text = models.TextField(
        default="Join our fitness club! Choose a membership plan that fits your needs. You'll need to sign in to subscribe.",
        help_text="Introduction text shown at the top of the membership page"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membership Plan Content"
        verbose_name_plural = "Membership Plan Content"
    
    def __str__(self):
        return f"Membership Plan Content (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the single instance of MembershipPlanContent"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class FeaturedProductsContent(models.Model):
    """
    Content model for Featured Products section on home page.
    Singleton pattern - only one instance should exist.
    """
    # Section header
    section_title = models.CharField(
        max_length=200,
        default="Featured Products",
        help_text="Title shown above the featured products section"
    )
    section_description = models.TextField(
        default="Hand-picked programs and equipment from our store",
        help_text="Description text shown below the title in the featured products section"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Featured Products Content"
        verbose_name_plural = "Featured Products Content"
    
    def __str__(self):
        return f"Featured Products Content (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the single instance of FeaturedProductsContent"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class AdminSettings(models.Model):
    """
    Admin settings for controlling various admin panel features.
    Singleton pattern - only one instance should exist.
    """
    show_platform_membership = models.BooleanField(
        default=True,
        help_text="Show/hide platform membership functions"
    )
    show_seller_membership = models.BooleanField(
        default=True,
        help_text="Show/hide seller membership functions"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Keep old field for backward compatibility during migration
    show_membership_functions = models.BooleanField(
        default=True,
        help_text="[Deprecated] Use show_platform_membership instead"
    )
    
    class Meta:
        verbose_name = "Admin Settings"
        verbose_name_plural = "Admin Settings"
    
    def __str__(self):
        return f"Admin Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Get or create the single instance of AdminSettings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj