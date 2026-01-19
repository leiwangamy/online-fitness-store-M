"""
Admin views for refund management
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from decimal import Decimal

from .models import Refund, Order
from services.stripe_refunds import create_stripe_refund, StripeRefundError, _to_cents


@staff_member_required
def admin_refund_queue(request):
    """
    List all refund requests awaiting admin approval.
    """
    refunds = Refund.objects.filter(status=Refund.STATUS_REQUESTED).select_related(
        'order', 'seller', 'order_item', 'created_by'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(refunds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'orders/admin_refund_queue.html', {
        'page_obj': page_obj,
    })


@staff_member_required
@transaction.atomic
def admin_approve_refund(request, refund_id):
    """
    Admin approves a refund request and processes it via Stripe.
    """
    refund = get_object_or_404(Refund, id=refund_id, status=Refund.STATUS_REQUESTED)
    order = refund.order
    
    if not order.payment_intent_id:
        messages.error(request, "Order missing Stripe payment reference. Cannot process refund.")
        return redirect('orders:admin_refund_queue')
    
    # Update refund status to processing
    refund.status = Refund.STATUS_PROCESSING
    refund.save(update_fields=["status"])
    
    try:
        # Process Stripe refund
        stripe_refund_id = create_stripe_refund(
            payment_intent_id=order.payment_intent_id,
            amount_cents=_to_cents(refund.amount),
            reason="requested_by_customer"
        )
        
        # Update refund with Stripe ID and mark as succeeded
        refund.stripe_refund_id = stripe_refund_id
        refund.status = Refund.STATUS_SUCCEEDED
        refund.save(update_fields=["stripe_refund_id", "status"])
        
        # Update order status
        # Check if all items in order are refunded
        from django.db.models import Sum
        total_refunded = Refund.objects.filter(
            order=order,
            status=Refund.STATUS_SUCCEEDED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if total_refunded >= order.total:
            order.status = Order.STATUS_REFUNDED
        else:
            order.status = Order.STATUS_PARTIALLY_REFUNDED
        order.save(update_fields=["status"])
        
        messages.success(request, f"Refund #{refund.id} approved and processed successfully via Stripe.")
    except StripeRefundError as e:
        refund.status = Refund.STATUS_FAILED
        refund.save(update_fields=["status"])
        messages.error(request, f"Stripe refund failed: {str(e)}")
    except Exception as e:
        refund.status = Refund.STATUS_FAILED
        refund.save(update_fields=["status"])
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('orders:admin_refund_queue')


@staff_member_required
@transaction.atomic
def admin_reject_refund(request, refund_id):
    """
    Admin rejects a refund request.
    """
    refund = get_object_or_404(Refund, id=refund_id, status=Refund.STATUS_REQUESTED)
    refund.status = Refund.STATUS_REJECTED
    refund.save(update_fields=["status"])
    
    messages.info(request, f"Refund request #{refund.id} has been rejected.")
    return redirect('orders:admin_refund_queue')

