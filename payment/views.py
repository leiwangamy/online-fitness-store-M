from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from members.models import Product, Order, OrderItem


@login_required
def checkout(request):
    """
    Checkout page:
    - Shows order summary
    - Checks stock
    - Calculates tax + shipping
    - On POST (and if stock is OK), creates order + order items,
      copies shipping snapshot from profile, clears cart, redirects to success.
    """
    # Cart is stored in session: { "product_id": quantity }
    cart = request.session.get("cart", {})

    # Case 1: empty cart
    if not cart:
        return render(request, "payment/checkout.html", {"empty": True})

    # Get products in cart
    product_ids = cart.keys()
    products = Product.objects.filter(pk__in=product_ids, is_active=True)
    product_map = {str(p.pk): p for p in products}

    items = []
    subtotal = Decimal("0.00")
    insufficient_items = []

    for pid, qty in cart.items():
        product = product_map.get(str(pid))
        if not product:
            continue

        # ----- Stock checks (physical products only) -----
        # Digital/service usually shouldn't be stock-checked the same way.
        # Physical products: try to use quantity_in_stock if present.
        if (not product.is_digital) and (not product.is_service):
            stock = getattr(product, "quantity_in_stock", None)
            if stock is not None and qty > stock:
                insufficient_items.append(
                    {
                        "product": product,
                        "requested": qty,
                        "available": stock,
                    }
                )

        # Line totals
        line_total = (product.price * qty).quantize(Decimal("0.01"))
        subtotal += line_total

        items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    subtotal = subtotal.quantize(Decimal("0.01"))

    # --- Tax (5%) ---
    TAX_RATE = Decimal("0.05")
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))

    # --- Shipping rules (combined logic) ---
    # Shipping only for physical products:
    has_physical_item = any(
        (not item["product"].is_digital) and (not item["product"].is_service)
        for item in items
    )

    if subtotal == 0:
        shipping = Decimal("0.00")
        shipping_label = "No shipping (empty cart)"
    elif not has_physical_item:
        shipping = Decimal("0.00")
        shipping_label = "No shipping (digital / service products only)"
    else:
        if subtotal >= Decimal("100.00"):
            shipping = Decimal("0.00")
            shipping_label = "Free shipping for physical orders over $100"
        else:
            shipping = Decimal("15.00")
            shipping_label = "Flat $15 shipping for physical products"

    total = (subtotal + tax + shipping).quantize(Decimal("0.01"))

    # If user clicks "Place Order"
    if request.method == "POST" and not insufficient_items:
        # In a real app you'd verify payment here.
        with transaction.atomic():
            # 1) Create the Order
            order = Order.objects.create(
                user=request.user,
                status="paid",  # for now, assume successful payment
                subtotal=subtotal,
                tax=tax,
                shipping=shipping,
                total=total,
            )

            # 1.5) COPY PROFILE → ORDER shipping snapshot (BEST PRACTICE)
            # Keeps historical shipping address even if user edits profile later.
            try:
                p = request.user.profile
                # If you also have name fields in profile, you can fill ship_name too.
                order.ship_phone = getattr(p, "phone", "") or ""
                order.ship_address1 = getattr(p, "address1", "") or ""
                order.ship_address2 = getattr(p, "address2", "") or ""
                order.ship_city = getattr(p, "city", "") or ""
                order.ship_province = getattr(p, "province", "") or ""
                order.ship_postal_code = getattr(p, "postal_code", "") or ""
                order.ship_country = getattr(p, "country", "") or ""

                order.save(
                    update_fields=[
                        "ship_phone",
                        "ship_address1",
                        "ship_address2",
                        "ship_city",
                        "ship_province",
                        "ship_postal_code",
                        "ship_country",
                    ]
                )
            except Exception:
                # If profile doesn't exist for some reason, don't crash checkout
                pass

            # 2) Create OrderItems and adjust inventory
            for item in items:
                product = item["product"]
                qty = item["quantity"]

                # unit price at purchase
                line_price = (item["line_total"] / qty).quantize(Decimal("0.01"))

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=line_price,
                )

                # Adjust inventory based on product type
                if product.is_digital:
                    # Digital: no stock change
                    continue

                if product.is_service:
                    # Limited seats only
                    if getattr(product, "service_seats", None) is not None:
                        new_seats = product.service_seats - qty
                        if new_seats < 0:
                            new_seats = 0  # safety
                        product.service_seats = new_seats
                        product.save(update_fields=["service_seats"])
                    continue

                # Physical products
                current_stock = getattr(product, "quantity_in_stock", None)
                if current_stock is not None:
                    new_stock = current_stock - qty
                    if new_stock < 0:
                        new_stock = 0  # safety
                    product.quantity_in_stock = new_stock
                    product.save(update_fields=["quantity_in_stock"])

            # 3) Clear cart after successful "payment"
            request.session["cart"] = {}
            request.session.modified = True

        # You can pass order id to success page later if you want:
        # return redirect("payment:success", order_id=order.id)
        return redirect("payment:success")

    context = {
        "empty": False,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "shipping_label": shipping_label,
        "total": total,
        "insufficient_items": insufficient_items,
    }
    return render(request, "payment/checkout.html", context)


@login_required
def success(request):
    """Simple success page after 'placing' the order."""
    return render(request, "payment/success.html")
