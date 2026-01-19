"""
Payment and Checkout Views Module

This module handles the checkout and payment processing flow for the e-commerce platform.

Key Features:
- Shopping cart checkout process
- Shipping calculation (flat rate or free shipping over threshold)
- Tax calculation (GST/HST)
- Support for physical products (shipping/pickup) and digital/service products (simplified checkout)
- Pickup location selection for physical products
- Order creation and processing
- Digital download generation and email delivery

Checkout Flow (Safe Payment Flow):
1. User views cart items and totals
2. For physical products: Select shipping or pickup, enter shipping address
3. For digital/service only: Simplified checkout (order summary only)
4. STEP 1: Order is created with status "pending" FIRST (ensures order exists in DB)
5. STEP 2: ALL OrderItems are created completely (ensures complete order data)
6. STEP 3: Order integrity is verified (all items saved successfully)
7. STEP 4: Payment is processed ONLY AFTER order is fully saved
8. STEP 5: If payment succeeds, order status updated to "paid"
9. Digital products: Download links generated and emailed (only after payment confirmed)
10. Services: Seats deducted from availability (only after payment confirmed)
11. Cart is cleared (only after payment confirmed)
12. User redirected to success page

CRITICAL SAFETY: Order is ALWAYS saved completely before payment processing begins.
This prevents the scenario where credit card is charged but order info is not saved.

Safe Order Processing Rules:
1. Use DB transaction for order creation (transaction.atomic() wrapper)
   - Order + all OrderItems created atomically (all-or-nothing)
2. Reserve/hold inventory when order is placed (not after payment)
   - Inventory/stock decremented IMMEDIATELY when order is created (status="pending")
   - Prevents two people from buying the last item simultaneously (no overselling)
   - Inventory is "held" for the pending order until payment succeeds or order expires
   - Expired orders (>30 minutes): Use `python manage.py expire_pending_orders` to release inventory
   - Run cleanup command periodically (e.g., every 5-10 minutes via cron/scheduled task)
3. Prevent double-charging
   - Use idempotency keys on payment gateway calls
   - Store payment_intent_id (unique constraint prevents duplicates)
   - Webhook handler: Check "if order already PAID, do nothing"

Shipping Logic:
- Physical products: Flat rate shipping or free over threshold
- Pickup orders: No shipping fee
- Digital/service only: No shipping required

Tax Calculation:
- GST/HST: 5% (configurable via TAX_RATE)
- Applied to subtotal before shipping

Constants:
- TAX_RATE: GST/HST rate (default: 5%)
- FREE_SHIP_OVER: Free shipping threshold (default: $100)
- FLAT_SHIP: Flat shipping rate (default: $15)
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from orders.forms import ShippingAddressForm

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
from orders.services import create_downloads_and_email, send_order_confirmation_email
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
            "first_name": getattr(profile, "first_name", "") or "",
            "last_name": getattr(profile, "last_name", "") or "",
            "phone": getattr(profile, "phone", "") or "",
            "address1": getattr(profile, "address1", "") or "",
            "address2": getattr(profile, "address2", "") or "",
            "city": getattr(profile, "city", "") or "",
            "province": getattr(profile, "province", "") or "",
            "postal_code": getattr(profile, "postal_code", "") or "",
            "country": getattr(profile, "country", "") or "Canada",
        }
    
    # Fallback if no profile - try to get name from user model
    user_first_name = getattr(user, "first_name", "") or ""
    user_last_name = getattr(user, "last_name", "") or ""
    return {
        "first_name": user_first_name,
        "last_name": user_last_name,
        "phone": "",
        "address1": "",
        "address2": "",
        "city": "",
        "province": "",
        "postal_code": "",
        "country": "Canada",
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
    
    # Check if there are any physical products (not digital, not service)
    # If cart contains only digital products OR service products (or both), skip shipping/pickup
    has_physical_products = any(
        (not getattr(i["product"], "is_digital", False)) and (not getattr(i["product"], "is_service", False))
        for i in items
    )
    
    # If no physical products (only digital/service), skip shipping/pickup and show simplified checkout
    if not has_physical_products:
        # Digital/service only - no shipping needed, no address required
        shipping = Decimal("0.00")
        shipping_label = "No shipping (digital / service only)"
        total = (subtotal + tax + shipping).quantize(Decimal("0.01"))
        
        # For POST requests, create order directly
        if request.method == "POST":
            if insufficient_items:
                messages.error(request, "Some items are out of stock. Please adjust your cart.")
                return redirect("payment:checkout")
            
            # Create order without shipping address
            with transaction.atomic():
                # STEP 1: Create order with status "pending" FIRST
                order = Order.objects.create(
                    user=request.user,
                    status=Order.STATUS_PENDING,  # Create as "pending" initially
                    subtotal=subtotal,
                    tax=tax,
                    shipping=shipping,
                    total=total,
                    is_pickup=False,
                    pickup_location=None,
                    # Use minimal shipping data from user profile
                    ship_name=request.user.get_full_name() or request.user.get_username(),
                    ship_phone="",
                    ship_address1="",
                    ship_address2="",
                    ship_city="",
                    ship_province="",
                    ship_postal_code="",
                    ship_country="Canada",
                )
                
                # STEP 2: Create ALL OrderItems completely BEFORE payment processing
                # RULE 1: Use DB transaction - order + items created atomically
                # RULE 2: Reserve/hold inventory when order is placed (not after payment)
                # This prevents two people from buying the last item simultaneously
                for i in items:
                    product = i["product"]
                    qty = int(i["quantity"])
                    line_total = Decimal(str(i["line_total"]))
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=Decimal(str(product.price)),
                    )
                    
                    # RULE 2: Reserve inventory immediately when order is placed
                    # This holds the inventory and prevents overselling
                    is_digital = bool(getattr(product, "is_digital", False))
                    is_service = bool(getattr(product, "is_service", False))
                    
                    if is_digital:
                        # Log digital product (no inventory to reserve)
                        log_purchase(
                            product=product,
                            quantity=qty,
                            change_type="ORDER",
                            created_by=request.user,
                            order=order,
                            note=f"Order #{order.id} - Digital product: {product.name} x{qty}"
                        )
                    elif is_service:
                        # Reserve service seats immediately
                        seats = getattr(product, "service_seats", None)
                        if seats is not None:
                            product.refresh_from_db()
                            product.service_seats = max(0, getattr(product, "service_seats", 0) - qty)
                            product.save(update_fields=["service_seats"])
                        log_purchase(
                            product=product,
                            quantity=qty,
                            change_type="ORDER",
                            created_by=request.user,
                            order=order,
                            note=f"Order #{order.id} - Service: {product.name} x{qty}"
                        )
                    else:
                        # Reserve physical product inventory immediately
                        stock = getattr(product, "quantity_in_stock", None)
                        if stock is not None:
                            adjust_inventory(
                                product=product,
                                delta=-qty,  # Negative to reduce stock (reserve it)
                                change_type="ORDER",
                                created_by=request.user,
                                order=order,
                                note=f"Order #{order.id} - {product.name} x{qty} (RESERVED)"
                            )
                
                # STEP 3: Verify all order items are saved successfully
                order_items_count = order.items.count()
                if order_items_count == 0:
                    raise ValueError("Order created but no order items were saved!")

                # STEP 4: Process payment (if you integrate payment gateway like Stripe)
                # IMPORTANT: Payment should only be processed AFTER order is fully saved
                # RULE 3: Prevent double-charging with idempotency key
                import uuid
                idempotency_key = str(uuid.uuid4())  # Generate unique idempotency key
                
                # TODO: Replace with actual payment gateway call (Stripe example):
                # payment_intent = stripe.PaymentIntent.create(
                #     amount=int(order.total * 100),  # Convert to cents
                #     currency='usd',
                #     idempotency_key=idempotency_key,  # Prevents double-charging
                #     metadata={'order_id': order.id}
                # )
                # payment_successful = payment_intent.status == 'succeeded'
                # payment_intent_id = payment_intent.id
                payment_successful = True  # TODO: Replace with actual payment gateway call
                payment_intent_id = f"test_{order.id}_{idempotency_key[:8]}"  # TODO: Use real payment_intent.id
                
                if payment_successful:
                    # RULE 3: Check if order already paid (webhook might have updated it)
                    # Refresh order from DB to check current status
                    order.refresh_from_db()
                    if order.status == Order.STATUS_PAID:
                        # Already paid (e.g., by webhook) - do nothing, prevent double-processing
                        messages.info(request, f"Order #{order.id} already processed.")
                        return redirect("payment:success")
                    
                    # RULE 3: Store payment_intent_id (unique constraint prevents double-charging)
                    try:
                        order.payment_intent_id = payment_intent_id
                        order.status = Order.STATUS_PAID
                        order.save(update_fields=['status', 'payment_intent_id'])
                    except Exception as e:
                        # payment_intent_id already exists - order was already paid
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Order {order.id} payment_intent_id {payment_intent_id} already exists: {e}")
                        messages.error(request, "Payment was already processed for this order.")
                        return redirect("payment:checkout")
                    
                    # RULE 2: Inventory was already reserved when order was created (STEP 2)
                    # No need to decrement again - inventory is held for this order
                    # If payment fails, inventory remains reserved (could add expiry/cleanup logic later)
                    
                    # Send order confirmation email (only after payment confirmed)
                    send_order_confirmation_email(request, order)
                    
                    # Create digital downloads and send email (if there are digital products)
                    create_downloads_and_email(request, order)
                    
                    _clear_cart(request)
                    request.session["last_order_id"] = order.id
                    messages.success(request, f"Order #{order.id} placed successfully!")
                    return redirect("payment:success")
                else:
                    # Payment failed - order remains "pending"
                    messages.error(request, "Payment processing failed. Please try again.")
                    return redirect("payment:checkout")
        
        # For GET requests, show simplified checkout (no shipping form)
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
                "digital_only": True,  # Flag to hide shipping/pickup form in template (applies to digital AND service products)
            },
        )
    
    # Physical products present - show shipping/pickup form
    # Get pickup locations for template
    try:
        pickup_locations = PickupLocation.objects.filter(is_active=True).order_by('display_order', 'name')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting pickup locations: {e}")
        pickup_locations = PickupLocation.objects.none()  # Empty queryset
    
    # For GET request, calculate shipping with default (not pickup)
    shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=False)
    total = (subtotal + tax + shipping).quantize(Decimal("0.01"))

    initial = _profile_initial(request.user)

    # ---------------- POST: place order ---------------- 
    if request.method == "POST":
        if insufficient_items:
            messages.error(request, "Some items are out of stock. Please adjust your cart.")
            return redirect("payment:checkout")

        try:
            form = ShippingAddressForm(request.POST, pickup_locations=pickup_locations)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating ShippingAddressForm with POST data: {e}")
            form = ShippingAddressForm(request.POST)
        
        if not form.is_valid():
            # Recalculate shipping based on form data (even if invalid, to show correct preview)
            is_pickup = form.data.get("fulfillment_method") == "pickup"
            shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=is_pickup)
            total = (subtotal + tax + shipping).quantize(Decimal("0.01"))
            
            # Convert queryset to list for template
            pickup_locations_list = list(pickup_locations) if pickup_locations else []
            
            # Get profile for displaying default address
            try:
                from profiles.models import Profile
                profile = getattr(request.user, "profile", None)
                if not profile:
                    profile, _ = Profile.objects.get_or_create(user=request.user)
            except Exception:
                profile = None
            
            # Add error message to help user understand what's wrong
            messages.error(request, "Please correct the errors in the form below to complete your order.")
            
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
                    "pickup_locations": pickup_locations_list,
                    "default_address": initial,
                    "profile": profile,
                },
            )

        form_data = form.cleaned_data
        
        # Get fulfillment_method from cleaned_data, fallback to raw POST data if not available
        fulfillment_method = form_data.get("fulfillment_method") or request.POST.get("fulfillment_method", "shipping")
        is_pickup = fulfillment_method == "pickup"
        
        # Get pickup_location_id from cleaned_data or raw POST data
        pickup_location = None
        if is_pickup:
            pickup_location_id = form_data.get("pickup_location_id")
            if not pickup_location_id:
                # Fallback to raw POST data and convert to int
                pickup_location_id_str = request.POST.get("pickup_location_id", "").strip()
                if pickup_location_id_str:
                    try:
                        pickup_location_id = int(pickup_location_id_str)
                    except (ValueError, TypeError):
                        pickup_location_id = None
            
            if pickup_location_id:
                try:
                    pickup_location = PickupLocation.objects.get(pk=pickup_location_id, is_active=True)
                except (PickupLocation.DoesNotExist, ValueError, TypeError):
                    pickup_location = None
                    # Log error for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Pickup location {pickup_location_id} not found or inactive for order")
        
        # Recalculate shipping based on pickup selection
        shipping, shipping_label = _calc_shipping(items, subtotal, is_pickup=is_pickup)
        total = (subtotal + tax + shipping).quantize(Decimal("0.01"))
        
        # Prepare shipping data - if pickup, use pickup location address
        if is_pickup and pickup_location:
            # For pickup, use user's name
            user_first = getattr(request.user, "first_name", "") or ""
            user_last = getattr(request.user, "last_name", "") or ""
            if not user_first and not user_last:
                # Try to get from profile
                try:
                    profile = request.user.profile
                    user_first = getattr(profile, "first_name", "") or ""
                    user_last = getattr(profile, "last_name", "") or ""
                except Exception:
                    pass
            ship_name = f"{user_first} {user_last}".strip() or request.user.get_username()
            
            shipping_data = {
                "ship_name": ship_name,
                "ship_phone": pickup_location.phone or "",
                "ship_address1": pickup_location.address1,
                "ship_address2": pickup_location.address2 or "",
                "ship_city": pickup_location.city,
                "ship_province": pickup_location.province,
                "ship_postal_code": pickup_location.postal_code,
                "ship_country": pickup_location.country,
            }
        else:
            # Combine first_name and last_name into ship_name
            first_name = form_data.get("first_name", "").strip()
            last_name = form_data.get("last_name", "").strip()
            ship_name = f"{first_name} {last_name}".strip()
            
            shipping_data = {
                "ship_name": ship_name,
                "ship_phone": form_data.get("phone", ""),
                "ship_address1": form_data.get("address1", ""),
                "ship_address2": form_data.get("address2", ""),
                "ship_city": form_data.get("city", ""),
                "ship_province": form_data.get("province", ""),
                "ship_postal_code": form_data.get("postal_code", ""),
                "ship_country": form_data.get("country", "Canada"),
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

            # STEP 1: Create order with status "pending" FIRST
            # This ensures order exists in database before any payment processing
            # Payment should only be processed AFTER order is fully saved
            order = Order.objects.create(
                user=request.user,
                status=Order.STATUS_PENDING,  # Create as "pending" initially
                subtotal=subtotal,
                tax=tax,
                shipping=shipping,
                total=total,
                is_pickup=is_pickup,
                pickup_location=pickup_location,
                **shipping_data,  # works if your Order has these fields
            )

            # STEP 2: Create ALL OrderItems completely BEFORE payment processing
            # RULE 1: Use DB transaction - order + items created atomically
            # RULE 2: Reserve/hold inventory when order is placed (not after payment)
            # This prevents two people from buying the last item simultaneously
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
                
                # RULE 2: Reserve inventory immediately when order is placed
                # This holds the inventory and prevents overselling
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
                    # Reserve service seats immediately
                    seats = getattr(product, "service_seats", None)
                    if seats is not None:
                        # Refresh from DB to get latest value
                        product.refresh_from_db()
                        product.service_seats = max(0, getattr(product, "service_seats", 0) - qty)
                        product.save(update_fields=["service_seats"])
                    log_purchase(
                        product=product,
                        quantity=qty,
                        change_type="ORDER",
                        created_by=request.user,
                        order=order,
                        note=f"Order #{order.id} - Service: {product.name} x{qty}"
                    )
                    continue
                
                # Reserve physical product inventory immediately
                stock = getattr(product, "quantity_in_stock", None)
                if stock is not None:
                    # Use the product instance (adjust_inventory will handle the update safely)
                    # We already checked stock availability earlier, so this should be safe
                    adjust_inventory(
                        product=product,
                        delta=-qty,  # Negative to reduce stock (reserve it)
                        change_type="ORDER",
                        created_by=request.user,
                        order=order,
                        note=f"Order #{order.id} - {product.name} x{qty} (RESERVED)"
                    )

            # STEP 3: Verify all order items are saved successfully
            # This ensures order data integrity before payment
            order_items_count = order.items.count()
            if order_items_count == 0:
                raise ValueError("Order created but no order items were saved!")

            # STEP 4: Process payment (if you integrate payment gateway like Stripe)
            # IMPORTANT: Payment should only be processed AFTER order is fully saved
            # RULE 3: Prevent double-charging with idempotency key
            import uuid
            idempotency_key = str(uuid.uuid4())  # Generate unique idempotency key
            
            # TODO: Replace with actual payment gateway call (Stripe example):
            # payment_intent = stripe.PaymentIntent.create(
            #     amount=int(order.total * 100),  # Convert to cents
            #     currency='usd',
            #     idempotency_key=idempotency_key,  # Prevents double-charging
            #     metadata={'order_id': order.id}
            # )
            # payment_successful = payment_intent.status == 'succeeded'
            # payment_intent_id = payment_intent.id
            payment_successful = True  # TODO: Replace with actual payment gateway call
            payment_intent_id = f"test_{order.id}_{idempotency_key[:8]}"  # TODO: Use real payment_intent.id
            
            if payment_successful:
                # RULE 3: Check if order already paid (webhook might have updated it)
                # Refresh order from DB to check current status
                order.refresh_from_db()
                if order.status == Order.STATUS_PAID:
                    # Already paid (e.g., by webhook) - do nothing, prevent double-processing
                    messages.info(request, f"Order #{order.id} already processed.")
                    return redirect("payment:success")
                
                # RULE 3: Store payment_intent_id (unique constraint prevents double-charging)
                try:
                    order.payment_intent_id = payment_intent_id
                    order.status = Order.STATUS_PAID
                    order.save(update_fields=['status', 'payment_intent_id'])
                except Exception as e:
                    # payment_intent_id already exists - order was already paid
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Order {order.id} payment_intent_id {payment_intent_id} already exists: {e}")
                    messages.error(request, "Payment was already processed for this order.")
                    return redirect("payment:checkout")
                
                # RULE 2: Inventory was already reserved when order was created (STEP 2)
                # No need to decrement again - inventory is held for this order
                # If payment fails, inventory remains reserved (could add expiry/cleanup logic later)
                
                # Send order confirmation email (only after payment confirmed)
                send_order_confirmation_email(request, order)
                
                # Create DigitalDownload rows + send email (if there are digital products)
                # (your service already uses get_or_create so it's safe)
                create_downloads_and_email(request, order, days_valid=7, max_downloads=0)

                _clear_cart(request)

                request.session["last_order_id"] = order.id
                messages.success(request, f"Order #{order.id} placed successfully!")
                return redirect("payment:success")
            else:
                # Payment failed - order remains "pending"
                # You can handle this case (show error, retry payment, etc.)
                messages.error(request, "Payment processing failed. Please try again.")
                # Optionally: delete the pending order or mark it for retry
                return redirect("payment:checkout")

        # If we get here, transaction failed - order was not saved
        messages.error(request, "Failed to create order. Please try again.")
        return redirect("payment:checkout")

    # ---------------- GET: show checkout ---------------- 
    # Get profile for displaying default address
    try:
        from profiles.models import Profile
        profile = getattr(request.user, "profile", None)
        if not profile:
            profile, _ = Profile.objects.get_or_create(user=request.user)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting profile: {e}")
        profile = None
    
    # Create form with pickup locations - use initial data, no validation errors on GET
    try:
        form = ShippingAddressForm(initial=initial, pickup_locations=pickup_locations)
    except Exception as e:
        # Fallback if form creation fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating ShippingAddressForm: {e}")
        try:
            form = ShippingAddressForm(initial=initial)
        except Exception as e2:
            logger.error(f"Error creating ShippingAddressForm without pickup_locations: {e2}")
            # Last resort - create form with minimal data
            form = ShippingAddressForm()
    
    # Convert queryset to list for template (safer for iteration)
    try:
        pickup_locations_list = list(pickup_locations) if pickup_locations else []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error converting pickup_locations to list: {e}")
        pickup_locations_list = []
    
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
            "pickup_locations": pickup_locations_list,  # Pass pickup locations as list for template
        },
    )


@login_required
def success(request):
    order_id = request.session.get("last_order_id")
    return render(request, "payment/success.html", {"order_id": order_id})
