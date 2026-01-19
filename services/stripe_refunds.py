"""
Stripe Refunds Service

This module handles all Stripe refund operations.
Keeps all Stripe-specific logic in one place for easier maintenance.
"""
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Initialize Stripe API key (only if stripe is available)
if STRIPE_AVAILABLE:
    try:
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    except Exception:
        stripe.api_key = None


class StripeRefundError(Exception):
    """Custom exception for Stripe refund errors"""
    pass


def _to_cents(amount) -> int:
    """
    Convert Decimal amount to cents (integer) for Stripe.
    
    Args:
        amount: Decimal amount in dollars
    
    Returns:
        int: Amount in cents
    """
    from decimal import Decimal
    return int((amount * Decimal("100")).quantize(Decimal("1")))


def create_stripe_refund(payment_intent_id: str, amount_cents: int, reason: str = None) -> str:
    """
    Create a refund in Stripe.
    
    Args:
        payment_intent_id: Stripe payment intent ID
        amount_cents: Refund amount in cents (integer)
        reason: Optional refund reason (e.g., "duplicate", "fraudulent", "requested_by_customer")
    
    Returns:
        str: Stripe refund ID
    
    Raises:
        StripeRefundError: If Stripe API call fails
        ImproperlyConfigured: If Stripe API key is not set or stripe package is not installed
    """
    if not STRIPE_AVAILABLE:
        raise ImproperlyConfigured("stripe package is not installed. Install it with: pip install stripe")
    
    if not stripe.api_key:
        raise ImproperlyConfigured("STRIPE_SECRET_KEY is not set in settings")
    
    if not payment_intent_id:
        raise StripeRefundError("Payment intent ID is required")
    
    try:
        refund_params = {
            "payment_intent": payment_intent_id,
            "amount": amount_cents,
        }
        
        # Add reason if provided
        if reason:
            refund_params["reason"] = reason
        
        refund = stripe.Refund.create(**refund_params)
        return refund["id"]
    except stripe.error.StripeError as e:
        raise StripeRefundError(f"Stripe error: {str(e)}")
    except Exception as e:
        raise StripeRefundError(f"Unexpected error: {str(e)}")


def get_stripe_refund(refund_id: str):
    """
    Retrieve a Stripe refund by ID.
    
    Args:
        refund_id: Stripe refund ID
    
    Returns:
        dict: Stripe refund object
    
    Raises:
        StripeRefundError: If Stripe API call fails
        ImproperlyConfigured: If Stripe API key is not set or stripe package is not installed
    """
    if not STRIPE_AVAILABLE:
        raise ImproperlyConfigured("stripe package is not installed. Install it with: pip install stripe")
    
    if not stripe.api_key:
        raise ImproperlyConfigured("STRIPE_SECRET_KEY is not set in settings")
    
    try:
        return stripe.Refund.retrieve(refund_id)
    except stripe.error.StripeError as e:
        raise StripeRefundError(f"Stripe error: {str(e)}")
    except Exception as e:
        raise StripeRefundError(f"Unexpected error: {str(e)}")

