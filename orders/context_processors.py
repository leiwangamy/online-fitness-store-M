"""
Context processor for staff notifications.
Shows pending refund requests count for staff users.
"""
from django.db import OperationalError, ProgrammingError


def staff_notifications(request):
    """
    Add staff notifications to template context.
    Shows pending refund requests count.
    """
    context = {
        'pending_refunds_count': 0,
        'has_pending_refunds': False,
    }
    
    # Only for staff users
    if not request.user.is_authenticated or not request.user.is_staff:
        return context
    
    try:
        from .models import Refund
        pending_count = Refund.objects.filter(status=Refund.STATUS_REQUESTED).count()
        context['pending_refunds_count'] = pending_count
        context['has_pending_refunds'] = pending_count > 0
    except (OperationalError, ProgrammingError):
        # Database tables might not exist yet
        pass
    except Exception:
        # Silently fail if there's any other error
        pass
    
    return context

