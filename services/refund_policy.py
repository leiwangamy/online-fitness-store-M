"""
Refund Policy Module

This module contains the business rules for refunds:
- Refund window (time-based eligibility)
- Auto-refund eligibility checks
- Seller permissions

All refund rules are centralized here so both seller and admin flows use the same logic.
"""
from django.utils import timezone
from datetime import timedelta

# Default refund window: 7 days from order creation
DEFAULT_REFUND_WINDOW_DAYS = 7


def is_within_refund_window(order, days=DEFAULT_REFUND_WINDOW_DAYS) -> bool:
    """
    Check if an order is within the refund window.
    
    Args:
        order: Order instance
        days: Number of days in the refund window (default: 7)
    
    Returns:
        bool: True if order is within refund window, False otherwise
    """
    if not order or not order.created_at:
        return False
    return timezone.now() <= order.created_at + timedelta(days=days)


def has_active_dispute(order) -> bool:
    """
    Check if an order has an active dispute.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if order has active dispute, False otherwise
    """
    if not order:
        return False
    # Check if order status is disputed
    if order.status == order.STATUS_DISPUTED:
        return True
    # Check if there are any refunds in requested/processing status (potential disputes)
    # This is a simple check - you might want to add a separate Dispute model later
    return False


def can_seller_auto_refund(order, seller, *, is_partial: bool = False, has_dispute: bool = None) -> bool:
    """
    Determine if a seller can auto-refund (without admin approval).
    
    Rules for auto-refund:
    - Order must be within refund window (7 days)
    - Order must not be disputed
    - Refund must be full (not partial)
    - Optional: Trusted sellers may have additional permissions (future enhancement)
    
    Args:
        order: Order instance
        seller: Seller instance
        is_partial: Whether this is a partial refund
        has_dispute: Whether order has active dispute (if None, will check automatically)
    
    Returns:
        bool: True if seller can auto-refund, False if admin approval required
    """
    if not order or not seller:
        return False
    
    # Check if order is disputed
    if has_dispute is None:
        has_dispute = has_active_dispute(order)
    
    if has_dispute or order.status == order.STATUS_DISPUTED:
        return False
    
    # Check refund window
    if not is_within_refund_window(order, days=DEFAULT_REFUND_WINDOW_DAYS):
        return False
    
    # Partial refunds require admin approval
    if is_partial:
        return False
    
    # Future: Trusted sellers might have extended permissions
    # if seller.is_trusted:
    #     return True
    
    # All checks passed - seller can auto-refund
    return True

