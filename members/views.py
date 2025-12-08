from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product
from decimal import Decimal


def home(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return render(request, "members/home.html", {"products": products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, "members/product_detail.html", {"product": product})

# --- Cart helpers ---

def _get_cart(request):
    """
    Get the cart dict from the session, or create an empty one.
    Cart format: { "product_id": quantity, ... }
    """
    cart = request.session.get("cart")
    if cart is None:
        cart = {}
        request.session["cart"] = cart
    return cart


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = _get_cart(request)

    product_id = str(product.pk)
    cart[product_id] = cart.get(product_id, 0) + 1

    request.session["cart"] = cart  # save back into session
    return redirect("cart_detail")


def remove_from_cart(request, pk):
    cart = _get_cart(request)
    product_id = str(pk)
    if product_id in cart:
        del cart[product_id]
        request.session["cart"] = cart
    return redirect("cart_detail")


def cart_detail(request):
    cart = _get_cart(request)

    items = []
    total = Decimal("0.00")

    # get the Product objects for items in cart
    product_ids = cart.keys()
    products = Product.objects.filter(pk__in=product_ids, is_active=True)

    product_map = {str(p.pk): p for p in products}

    for pid, qty in cart.items():
        product = product_map.get(pid)
        if not product:
            continue
        line_total = product.price * qty
        total += line_total
        items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    context = {
        "items": items,
        "total": total,
    }
    return render(request, "members/cart.html", context)


# --- Payment / checkout ---

@login_required
def payment(request):
    """
    Simple 'payment' page that requires login.
    In real life you'd integrate Stripe/PayPal etc.
    Here we just show the cart and simulate success.
    """
    cart = _get_cart(request)

    if not cart:
        return render(request, "members/payment.html", {"empty": True})

    # Build the same summary as in cart_detail
    items = []
    total = Decimal("0.00")
    product_ids = cart.keys()
    products = Product.objects.filter(pk__in=product_ids, is_active=True)
    product_map = {str(p.pk): p for p in products}

    for pid, qty in cart.items():
        product = product_map.get(pid)
        if not product:
            continue
        line_total = product.price * qty
        total += line_total
        items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    if request.method == "POST":
        # Here you would process real payment.
        # We'll just pretend it's successful and clear the cart.
        request.session["cart"] = {}
        return render(request, "members/payment_success.html", {"total": total})

    return render(request, "members/payment.html", {"items": items, "total": total})

