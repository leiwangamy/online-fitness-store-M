"""
Decorators for seller views to check permissions
"""
from functools import wraps
from django.shortcuts import redirect
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

