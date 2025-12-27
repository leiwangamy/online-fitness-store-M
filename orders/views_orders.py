from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, render

from .models import Order, OrderItem, DigitalDownload

from products.inventory import adjust_inventory

@login_required
def my_order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    items = (
        OrderItem.objects
        .filter(order=order)
        .select_related("product")
    )

    # Auto-create download records for digital products if they don't exist
    # This helps with orders created before downloads were set up
    digital_products = []
    for oi in items:
        p = oi.product
        is_digital = bool(getattr(p, "is_digital", False))
        has_file = bool(getattr(p, "digital_file", None))
        has_url = bool(getattr(p, "digital_url", None))
        if is_digital and (has_file or has_url):
            digital_products.append(p)

    if digital_products:
        # Avoid race conditions creating duplicates
        from datetime import timedelta
        from django.utils import timezone
        expires_at = timezone.now() + timedelta(days=30)  # 30 days expiry
        
        with transaction.atomic():
            for p in digital_products:
                DigitalDownload.objects.get_or_create(
                    order=order,
                    product=p,
                    defaults={
                        "expires_at": expires_at,
                        "max_downloads": 0,  # 0 = unlimited downloads
                    }
                )

    downloads = (
        DigitalDownload.objects
        .filter(order=order)
        .select_related("product")
    )

    return render(request, "orders/my_order_detail.html", {
        "order": order,
        "items": items,
        "downloads": downloads,
    })

@login_required
def my_orders(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )
    return render(request, "orders/my_orders.html", {"orders": orders})