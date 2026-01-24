from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from .models import CartItem
from .utils import (
    get_cart_items,
    add_to_session_cart,
    remove_from_session_cart,
    update_session_cart_quantity,
)


TAX_RATE = Decimal("0.05")  # change if you want


def _is_digital_or_service(product: Product) -> bool:
    return bool(getattr(product, "is_digital", False) or getattr(product, "is_service", False))


def _max_stock(product: Product) -> int:
    """
    Digital/service: unlimited (use a large number)
    Physical: quantity_in_stock (default 0)
    """
    if _is_digital_or_service(product):
        return 999999

    return int(getattr(product, "quantity_in_stock", 0) or 0)


@transaction.atomic
def add_to_cart(request, pk):
    """
    Add to cart or update quantity for a single product.
    Works for both authenticated and anonymous users.
    - GET: add 1 (like "Add to Cart" button)
    - POST: supports quantity + override=True
    """
    product = get_object_or_404(Product, pk=pk, is_active=True)

    max_stock = _max_stock(product)
    if max_stock <= 0 and not _is_digital_or_service(product):
        # no stock for physical product
        return redirect("cart:cart_detail")

    # digital/service forced to 1
    if _is_digital_or_service(product):
        quantity = 1
        override = True
    else:
        if request.method == "POST":
            quantity = int(request.POST.get("quantity", 1))
            override = request.POST.get("override") == "True"
        else:
            quantity = 1
            override = False

    if request.user.is_authenticated:
        # Authenticated users: use database
        cart_item, _created = CartItem.objects.select_for_update().get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": 0},
        )

        if quantity < 1:
            cart_item.delete()
            return redirect("cart:cart_detail")

        if override:
            new_qty = min(quantity, max_stock)
        else:
            new_qty = min(cart_item.quantity + quantity, max_stock)

        cart_item.quantity = new_qty
        cart_item.save(update_fields=["quantity"])
    else:
        # Anonymous users: use session
        product_id_str = str(pk)
        cart = request.session.get('cart', {})
        current_qty = cart.get(product_id_str, 0)

        if quantity < 1:
            remove_from_session_cart(request, pk)
            return redirect("cart:cart_detail")

        if override:
            new_qty = min(quantity, max_stock)
        else:
            new_qty = min(current_qty + quantity, max_stock)

        update_session_cart_quantity(request, pk, new_qty)

    return redirect("cart:cart_detail")


def remove_from_cart(request, pk):
    """Remove item from cart for both authenticated and anonymous users"""
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user, product_id=pk).delete()
    else:
        remove_from_session_cart(request, pk)
    
    return redirect("cart:cart_detail")


@transaction.atomic
def update_cart_item(request, pk):
    """
    Update quantity in cart (POST only).
    Works for both authenticated and anonymous users.
    """
    if request.method != "POST":
        return redirect("cart:cart_detail")

    product = get_object_or_404(Product, pk=pk, is_active=True)

    if _is_digital_or_service(product):
        quantity = 1
    else:
        quantity = int(request.POST.get("quantity", 1))

    if request.user.is_authenticated:
        # Authenticated users: use database
        item = get_object_or_404(CartItem.objects.select_for_update(), user=request.user, product=product)

        max_stock = _max_stock(product)
        if max_stock <= 0:
            item.delete()
            return redirect("cart:cart_detail")

        if quantity < 1:
            item.delete()
        else:
            item.quantity = min(quantity, max_stock)
            item.save(update_fields=["quantity"])
    else:
        # Anonymous users: use session
        max_stock = _max_stock(product)
        if max_stock <= 0:
            remove_from_session_cart(request, pk)
            return redirect("cart:cart_detail")

        update_session_cart_quantity(request, pk, quantity)

    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    Cart detail page - works for both authenticated and anonymous users.
    Anonymous users are redirected to login at checkout.
    """
    items = get_cart_items(request)

    subtotal = Decimal("0.00")
    for item in items:
        subtotal += item["line_total"]

    # Calculate GST (5%) on all items
    gst = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    # Calculate PST (7%) only on items that charge PST
    pst_subtotal = Decimal("0.00")
    for item in items:
        if getattr(item["product"], "charge_pst", False):
            pst_subtotal += item["line_total"]
    pst = (pst_subtotal * Decimal("0.07")).quantize(Decimal("0.01"))
    tax = gst + pst
    total_with_tax = (subtotal + gst + pst).quantize(Decimal("0.01"))

    context = {
        "items": items,
        "subtotal": subtotal,
        "gst": gst,
        "pst": pst,
        "tax": tax,
        "total_with_tax": total_with_tax,
    }
    return render(request, "cart/cart.html", context)
