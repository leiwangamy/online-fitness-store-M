def cart_context(request):
    """Add cart count to template context"""
    from django.db import OperationalError, ProgrammingError
    
    context = {}
    cart_count = 0
    
    try:
        from .models import CartItem
        
        if request.user.is_authenticated:
            # Count cart items for authenticated users
            cart_count = CartItem.objects.filter(
                user=request.user,
                product__is_active=True
            ).count()
        else:
            # For anonymous users, count from session cart
            cart = request.session.get('cart', {})
            cart_count = sum(cart.values()) if cart else 0
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - use session cart only
        cart = request.session.get('cart', {})
        cart_count = sum(cart.values()) if cart else 0
    except Exception:
        # Any other error - default to 0
        cart_count = 0
    
    context['cart_item_count'] = cart_count
    return context

