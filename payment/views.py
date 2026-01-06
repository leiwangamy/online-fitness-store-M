from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import ShippingAddressForm

# ---------- IMPORTANT ----------
# Adjust these imports to match your project structure.
# Recommended structure:
#   products app -> Product
#   orders app   -> Order, OrderItem, DigitalDownload
try:
    from products.models import Product
except Exception:
    # fallback if your Product is still inside members app
    from members.models import Product

from cart.models import CartItem
from orders.models import Order, OrderItem, PickupLocation
from orders.services import create_downloads_and_email
from products.inventory import adjust_inventory, log_purchase


TAX_RATE = Decimal("0.05")          # GST 5%
FREE_SHIP_OVER = Decimal("100.00")
FLAT_SHIP = Decimal("15.00")


def _get_cart_items(request):
    """
    Get cart items from database (CartItem model).
    Returns a list of cart items with product and quantity.
    """
    return CartItem.objects.filter(
        user=request.user,
        product__is_active=True
    ).select_related("product").order_by("-added_at")


def _clear_cart(request) -> None:
    """Delete all cart items for the user."""
    CartItem.objects.filter(user=request.user).delete()


def _profile_initial(user) -> dict:
    """
    Prefill shipping form from profile if exists.
    Uses Profile model from profiles app (related_name="profile").
    """
    try:
        profile = getattr(user, "profile", None)
        if not profile:
            from profiles.models import Profile
            profile, _ = Profile.objects.get_or_create(user=user)
    except Exception:
        profile = None

    if profile:
        return {
            "ship_name": user.get_full_name() or user.get_username(),
            "ship_phone": getattr(profile, "phone", "") or "",
            "ship_address1": getattr(profile, "address1", "") or "",
            "ship_address2": getattr(profile, "address2", "") or "",
            "ship_city": getattr(profile, "city", "") or "",
            "ship_province": getattr(profile, "province", "") or "",
            "ship_postal_code": getattr(profile, "postal_code", "") or "",
            "ship_country": getattr(profile, "country", "") or "Canada",
        }
    
    # Fallback if no profile
    return {
        "ship_name": user.get_full_name() or user.get_username(),
        "ship_phone": "",
        "ship_address1": "",
        "ship_address2": "",
        "ship_city": "",
        "ship_province": "",
        "ship_postal_code": "",
        "ship_country": "Canada",
    }


def _calc_shipping(items: list, subtotal: Decimal, is_pickup: bool = False) -> tuple[Decimal, str]:
    """
    Shipping only applies if there is at least one physical item.
    Physical item = not digital and not service.
    Pickup orders have no shipping fee.
    """
    # Pickup orders have no shipping
    if is_pickup:
        return Decimal("0.00"), "No shipping (pickup order)"
    
    has_physical = any(
        (not getattr(i["product"], "is_digital", False)) and (not getattr(i["product"], "is_service", False))
        for i in items
    )

    if subtotal <= 0:
        return Decimal("0.00"), "No shipping (empty cart)"
    if not has_physical:
        return Decimal("0.00"), "No shipping (digital / service only)"
    if subtotal >= FREE_SHIP_OVER:
        return Decimal("0.00"), f"Free shipping for physical orders over ${FREE_SHIP_OVER}"
    return FLAT_SHIP, f"Flat ${FLAT_SHIP} shipping for physical products"


@login_required
def checkout(request):
    # Get cart items from database
    cart_items = _get_cart_items(request)
    if not cart_items.exists():
        return render(request, "payment/checkout.html", {"empty": True})

    items = []
    subtotal = Decimal("0.00")
    insufficient_items = []

    for cart_item in cart_items:
        product = cart_item.product
        qty = cart_item.quantity

        # stock check only for physical items
        is_digital = bool(getattr(product, "is_digital", False))
        is_service = bool(getattr(product, "is_service", False))

        if (not is_digital) and (not is_service):
            stock = getattr(product, "quantity_in_stock", None)
            if stock is not None and qty > stock:
                insufficient_items.append(
                    {"product": product, "requested": qty, "available": stock}
                )

        line_total = (Decimal(str(product.price)) * qty).quantize(Decimal("0.01"))
        subtotal += line_total

        items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    subtotal = subtotal.quantize(Decimal("0.01"))
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    
    # Get pickup locations for template
    pickup_locations = PickupLocation.objects.filter(is_active=True).order_by('display_order', 'name')
    
    # For GET request, calculate shipping with default (not pickup)
    shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=False)
    total = (subtotal + tax + shipping).quantize(Decimal("0.01"))

    initial = _profile_initial(request.user)

    # ---------------- POST: place order ---------------- 
    if request.method == "POST":
        if insufficient_items:
            messages.error(request, "Some items are out of stock. Please adjust your cart.")
            return redirect("payment:checkout")

        form = ShippingAddressForm(request.POST)
        if not form.is_valid():
            # Recalculate shipping based on form data (even if invalid, to show correct preview)
            is_pickup = form.data.get("fulfillment_method") == "pickup"
            shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=is_pickup)
            total = (subtotal + tax + shipping).quantize(Decimal("0.01"))
            
            return render(
                request,
                "payment/checkout.html",
                {
                    "empty": False,
                    "items": items,
                    "subtotal": subtotal,
                    "tax": tax,
                    "shipping": shipping,
                    "shipping_label": shipping_label,
                    "total": total,
                    "insufficient_items": insufficient_items,
                    "form": form,
                    "pickup_locations": pickup_locations,
                    "default_address": initial,
                },
            )

        form_data = form.cleaned_data
        fulfillment_method = form_data.get("fulfillment_method", "shipping")
        is_pickup = fulfillment_method == "pickup"
        pickup_location = form_data.get("pickup_location_id") if is_pickup else None
        
        # Recalculate shipping based on pickup selection
        shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=is_pickup)
        total = (subtotal + tax + shipping).quantize(Decimal("0.01"))
        
        # Prepare shipping data - if pickup, use pickup location address
        if is_pickup and pickup_location:
            shipping_data = {
                "ship_name": request.user.get_full_name() or request.user.get_username(),
                "ship_phone": pickup_location.phone or "",
                "ship_address1": pickup_location.address1,
                "ship_address2": pickup_location.address2 or "",
                "ship_city": pickup_location.city,
                "ship_province": pickup_location.province,
                "ship_postal_code": pickup_location.postal_code,
                "ship_country": pickup_location.country,
            }
        else:
            shipping_data = {
                "ship_name": form_data.get("ship_name", ""),
                "ship_phone": form_data.get("ship_phone", ""),
                "ship_address1": form_data.get("ship_address1", ""),
                "ship_address2": form_data.get("ship_address2", ""),
                "ship_city": form_data.get("ship_city", ""),
                "ship_province": form_data.get("ship_province", ""),
                "ship_postal_code": form_data.get("ship_postal_code", ""),
                "ship_country": form_data.get("ship_country", "Canada"),
            }

        with transaction.atomic():
            # Lock products for safer inventory updates
            physical_ids = [
                i["product"].pk
                for i in items
                if (not getattr(i["product"], "is_digital", False))
                and (not getattr(i["product"], "is_service", False))
                and getattr(i["product"], "quantity_in_stock", None) is not None
            ]
            if physical_ids:
                # Actually fetch and lock the products
                locked_products = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=physical_ids)}
            else:
                locked_products = {}

            order = Order.objects.create(
                user=request.user,
                status="paid",  # make sure your model choices use "paid" (lowercase) if that's what you set
                subtotal=subtotal,
                tax=tax,
                shipping=shipping,
                total=total,
                is_pickup=is_pickup,
                pickup_location=pickup_location,
                **shipping_data,  # works if your Order has these fields
            )

            # Create OrderItems and update inventory
            for i in items:
                product = i["product"]
                qty = int(i["quantity"])
                line_total = Decimal(str(i["line_total"]))

                # Create OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=Decimal(str(product.price)),  # unit price at purchase
                )

                # Inventory update and logging
                is_digital = bool(getattr(product, "is_digital", False))
                is_service = bool(getattr(product, "is_service", False))

                if is_digital:
                    # Log digital product purchase (no stock to update)
                    log_purchase(
                        product=product,
                        quantity=qty,
                        change_type="ORDER",
                        created_by=request.user,
                        order=order,
                        note=f"Order #{order.id} - Digital product: {product.name} x{qty}"
                    )
                    continue

                if is_service:
                    # For services, update service_seats
                    seats = getattr(product, "service_seats", None)
                    if seats is not None:
                        # Refresh from DB to get latest value
                        product.refresh_from_db()
                        product.service_seats = max(0, getattr(product, "service_seats", 0) - qty)
                        product.save(update_fields=["service_seats"])
                    # Log service purchase (no physical stock to update)
                    log_purchase(
                        product=product,
                        quantity=qty,
                        change_type="ORDER",
                        created_by=request.user,
                        order=order,
                        note=f"Order #{order.id} - Service: {product.name} x{qty}"
                    )
                    continue

                # For physical products, update quantity_in_stock using adjust_inventory
                # This will update stock and create an inventory log entry
                stock = getattr(product, "quantity_in_stock", None)
                if stock is not None:
                    # Use the product instance (adjust_inventory will handle the update safely)
                    # We already checked stock availability earlier, so this should be safe
                    adjust_inventory(
                        product=product,
                        delta=-qty,  # Negative to reduce stock
                        change_type="ORDER",
                        created_by=request.user,
                        order=order,
                        note=f"Order #{order.id} - {product.name} x{qty}"
                    )

            # Create DigitalDownload rows + send email
            # (your service already uses get_or_create so it’s safe)
            create_downloads_and_email(request, order, days_valid=7, max_downloads=0)

            _clear_cart(request)

        request.session["last_order_id"] = order.id
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("payment:success")

    # ---------------- GET: show checkout ----------------
    # Get profile for displaying default address
    try:
        from profiles.models import Profile
        profile = getattr(request.user, "profile", None)
        if not profile:
            profile, _ = Profile.objects.get_or_create(user=request.user)
    except Exception:
        profile = None
    
    form = ShippingAddressForm(initial=initial)
    return render(
        request,
        "payment/checkout.html",
        {
            "empty": False,
            "items": items,
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "shipping_label": shipping_label,
            "total": total,
            "insufficient_items": insufficient_items,
            "form": form,
            "profile": profile,  # Pass profile to display default address
            "default_address": initial,  # Pass initial values for display
            "pickup_locations": pickup_locations,  # Pass pickup locations for template
        },
    )


@login_required
def success(request):
    order_id = request.session.get("last_order_id")
    return render(request, "payment/success.html", {"order_id": order_id})
