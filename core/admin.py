from django.contrib import admin
from django.utils.html import format_html
from .models import CompanyInfo, UserDeletion, BlogPost, BlogPostImage, MembershipPlanContent


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    """Admin interface for editing company contact information"""
    
    list_display = ['phone', 'email', 'updated_at']
    fieldsets = (
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Location & Description', {
            'fields': ('address', 'description')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


@admin.register(UserDeletion)
class UserDeletionAdmin(admin.ModelAdmin):
    """Admin interface for viewing deleted user accounts"""
    
    list_display = ['user', 'user_email', 'deleted_at', 'days_remaining', 'can_recover']
    list_filter = ['deleted_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'deleted_at', 'days_until_permanent', 'can_recover']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'deleted_at', 'reason')
        }),
        ('Deletion Status', {
            'fields': ('days_until_permanent', 'can_recover'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def days_remaining(self, obj):
        days = obj.days_until_permanent
        if days == 0:
            return "Permanent"
        return f"{days} days"
    days_remaining.short_description = "Days Remaining"
    
    def has_add_permission(self, request):
        return False  # Deletions are created through the deletion process


class BlogPostImageInline(admin.TabularInline):
    """Inline admin for managing multiple blog post images"""
    model = BlogPostImage
    extra = 1  # Show one empty form by default
    can_delete = True  # Allow deleting images
    fields = ('image', 'alt_text', 'display_order', 'is_main')
    verbose_name = "Image"
    verbose_name_plural = "Images"
    # Images are completely optional - blogs can be saved without any images
    # Empty forms will be automatically skipped by Django


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for managing blog posts"""
    
    list_display = ['title', 'author', 'is_published', 'published_date', 'view_count', 'created_at', 'image_count']
    list_filter = ['is_published', 'published_date', 'created_at', 'author']
    search_fields = ['title', 'content', 'excerpt', 'author']
    readonly_fields = ['created_at', 'updated_at', 'view_count']
    date_hierarchy = 'published_date'
    inlines = [BlogPostImageInline]
    
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'slug', 'author')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image'),
            'description': 'Note: You can also add multiple images using the "Images" section below.'
        }),
        ('Publication', {
            'fields': ('is_published', 'published_date')
        }),
        ('Statistics', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_prepopulated_fields(self, request, obj=None):
        # Only prepopulate slug when creating new objects
        if obj is None:  # creating a new object
            return {'slug': ('title',)}
        return {}  # don't prepopulate when editing existing objects
    
    def get_readonly_fields(self, request, obj=None):
        # Make slug readonly after creation to prevent broken URLs
        readonly = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly.append('slug')
        return readonly
    
    def image_count(self, obj):
        """Display the number of images for this blog post"""
        if obj.pk:
            count = obj.images.count()
            return f"{count} image{'s' if count != 1 else ''}"
        return "0 images"
    image_count.short_description = "Images"


@admin.register(MembershipPlanContent)
class MembershipPlanContentAdmin(admin.ModelAdmin):
    """Admin interface for editing membership plans page header/intro"""
    
    list_display = ['page_title', 'updated_at']
    
    fieldsets = (
        ('Page Header', {
            'fields': ('page_title', 'intro_text'),
            'description': 'Note: Actual membership plans are managed in the Members app under "Membership Plans".'
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton pattern)
        return not MembershipPlanContent.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion to maintain the singleton pattern
        return False
