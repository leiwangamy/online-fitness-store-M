from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import OperationalError, ProgrammingError


def contact_page(request):
    """Display company contact information"""
    company_info = None
    
    try:
        from .models import CompanyInfo
        company_info = CompanyInfo.get_instance()
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - show static content only
        company_info = None
    except Exception:
        # Any other database error - show static content
        company_info = None
    
    return render(request, 'core/contact.html', {
        'company_info': company_info
    })


def blog_page(request):
    """Display blog page with list of published posts"""
    posts = []
    page_obj = None
    
    try:
        from .models import BlogPost
        
        posts = BlogPost.objects.filter(is_published=True).prefetch_related('images')
        
        # Pagination: 10 posts per page
        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - show static content only
        from django.core.paginator import Paginator as PaginatorClass
        paginator = PaginatorClass([], 10)
        page_obj = paginator.get_page(1)
    except Exception:
        # Any other database error - show static content
        from django.core.paginator import Paginator as PaginatorClass
        paginator = PaginatorClass([], 10)
        page_obj = paginator.get_page(1)
    
    return render(request, 'core/blog.html', {
        'page_obj': page_obj,
        'posts': page_obj
    })


def blog_detail(request, slug):
    """Display individual blog post detail page"""
    post = None
    
    try:
        from .models import BlogPost
        
        post = get_object_or_404(
            BlogPost.objects.prefetch_related('images'),
            slug=slug,
            is_published=True
        )
        
        # Increment view count
        post.view_count += 1
        post.save(update_fields=['view_count'])
        
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - return 404
        from django.http import Http404
        raise Http404("Blog post not found - database not available")
    except Exception:
        # Any other database error - return 404
        from django.http import Http404
        raise Http404("Blog post not found")
    
    return render(request, 'core/blog_detail.html', {
        'post': post
    })
