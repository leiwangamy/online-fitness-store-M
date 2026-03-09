"""
Decorators for seller views to check permissions
"""
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse


def seller_required(view_func):
    """
    Decorator to ensure user is logged in and has an approved seller profile.
    Redirects to seller application page if not approved.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access the seller dashboard.")
            return redirect('account_login')
        
        try:
            from .models import Seller
            seller = request.user.seller
            if seller.status != Seller.STATUS_APPROVED:
                if seller.status == Seller.STATUS_PENDING:
                    messages.info(
                        request,
                        "Your seller application is pending approval. "
                        "You'll be able to add products once approved."
                    )
                    return redirect('sellers:application_status')
                elif seller.status == Seller.STATUS_REJECTED:
                    messages.warning(
                        request,
                        "Your seller application was rejected. "
                        "Please contact support if you believe this is an error."
                    )
                    return redirect('sellers:application_status')
        except AttributeError:
            # User doesn't have a seller profile
            messages.info(request, "You need to apply to become a seller first.")
            return redirect('sellers:apply')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def admin_or_seller_required(view_func):
    """
    Decorator that allows both:
    1. Approved sellers to access their own dashboard
    2. Staff/admins to view any seller's dashboard in read-only mode
    
    When accessed by admin, expects seller_id in GET parameter or kwargs.
    Sets request.is_read_only = True for admin access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access the seller dashboard.")
            return redirect('account_login')
        
        from .models import Seller
        
        # Check if admin is accessing another seller's dashboard
        seller_id = request.GET.get('seller_id') or kwargs.get('seller_id')
        
        if seller_id and request.user.is_staff:
            # Admin viewing another seller's dashboard
            seller = get_object_or_404(Seller, id=seller_id)
            request.is_read_only = True
            request.viewed_seller = seller
            return view_func(request, *args, **kwargs)
        
        # Regular seller access - use existing seller_required logic
        # Try to access seller - Django raises RelatedObjectDoesNotExist if it doesn't exist
        try:
            seller = request.user.seller
        except Exception:
            # Catch any exception (including RelatedObjectDoesNotExist which isn't directly importable)
            # RelatedObjectDoesNotExist is raised when accessing a reverse relation that doesn't exist
            messages.info(request, "You need to apply to become a seller first.")
            return redirect('sellers:apply')
        
        # Now we know seller exists, check status
        if seller.status != Seller.STATUS_APPROVED:
            if seller.status == Seller.STATUS_PENDING:
                messages.info(
                    request,
                    "Your seller application is pending approval. "
                    "You'll be able to add products once approved."
                )
                return redirect('sellers:application_status')
            elif seller.status == Seller.STATUS_REJECTED:
                messages.warning(
                    request,
                    "Your seller application was rejected. "
                    "Please contact support if you believe this is an error."
                )
                return redirect('sellers:application_status')
        
        request.is_read_only = False
        request.viewed_seller = seller
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

