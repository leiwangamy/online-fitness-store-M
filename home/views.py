from django.shortcuts import render
from django.core.paginator import Paginator
from django.db import OperationalError, ProgrammingError


def home(request):
    """
    Home page with hero section, featured products, and latest blog posts
    Handles database errors gracefully - shows static content if database is not available
    """
    featured_products = []
    latest_blog_posts = []
    content = None
    
    # Try to get products from database, but handle errors gracefully
    try:
        from products.models import Product, Category
        
        # Get featured products (limit to 3)
        # Only show active products that are marked as featured
        # Exclude seller products - only admin-curated products should be featured
        featured_products = Product.objects.filter(
            is_featured=True,
            is_active=True,
            seller__isnull=True  # Only products without a seller (admin-created)
        ).select_related("category").prefetch_related("images")[:3]
        
        # If no featured products, show some active products as fallback
        # Exclude seller products from fallback as well
        if not featured_products.exists():
            featured_products = Product.objects.filter(
                is_active=True,
                seller__isnull=True  # Only show admin-created products in fallback
            ).select_related("category").prefetch_related("images")[:3]
        
        # Get content from model (singleton pattern) with fallback
        try:
            from core.models import FeaturedProductsContent
            content = FeaturedProductsContent.get_instance()
        except (ImportError, AttributeError, Exception):
            content = None
        
        # Get latest blog post (only 1, only published)
        try:
            from core.models import BlogPost
            latest_blog_posts = BlogPost.objects.filter(
                is_published=True
            ).prefetch_related("images")[:1]
        except (ImportError, AttributeError, Exception):
            latest_blog_posts = []
            
    except (OperationalError, ProgrammingError) as e:
        # Database tables don't exist - show static content only
        # This happens when database is not set up or tables are missing
        featured_products = []
        latest_blog_posts = []
        content = None
    except Exception as e:
        # Any other database error - show static content
        featured_products = []
        latest_blog_posts = []
        content = None
    
    context = {
        "featured_products": featured_products,
        "latest_blog_posts": latest_blog_posts,
        "content": content,
    }
    
    return render(request, "home/home.html", context)
