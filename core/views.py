from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import CompanyInfo, BlogPost


def contact_page(request):
    """Display company contact information"""
    company_info = CompanyInfo.get_instance()
    return render(request, 'core/contact.html', {
        'company_info': company_info
    })


def blog_page(request):
    """Display blog page with list of published posts"""
    posts = BlogPost.objects.filter(is_published=True).prefetch_related('images')
    
    # Pagination: 10 posts per page
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/blog.html', {
        'page_obj': page_obj,
        'posts': page_obj
    })


def blog_detail(request, slug):
    """Display individual blog post detail page"""
    post = get_object_or_404(
        BlogPost.objects.prefetch_related('images'),
        slug=slug,
        is_published=True
    )
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    return render(request, 'core/blog_detail.html', {
        'post': post
    })
