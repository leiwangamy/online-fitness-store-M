import logging
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import DigitalDownload

logger = logging.getLogger(__name__)


def send_order_confirmation_email(request, order):
    """
    Send order confirmation email for ALL orders (physical, digital, or mixed).
    This includes a link to view the order details.
    """
    to_email = getattr(getattr(order, "user", None), "email", None)
    if not to_email:
        return
    
    # Build the order detail page URL
    order_path = reverse("orders:my_order_detail", args=[order.id])
    
    # Build a login URL that redirects to that order after login
    login_path = reverse("account_login")
    next_param = quote(order_path, safe="")
    login_path_with_next = f"{login_path}?next={next_param}"
    
    # Make absolute URLs
    order_url = request.build_absolute_uri(order_path)
    login_url = request.build_absolute_uri(login_path_with_next)
    
    subject = f"Order Confirmation - Order #{order.id}"
    message = (
        f"Thank you for your order!\n\n"
        f"Order Number: #{order.id}\n"
        f"Total: ${order.total}\n\n"
        f"View your order details:\n"
        f"{login_url}\n\n"
        f"If you're already signed in, you can view your order here:\n"
        f"{order_url}\n\n"
        f"We'll send you another email if your order contains digital downloads.\n"
    )
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {e}")


def create_downloads_and_email(request, order, days_valid=7, max_downloads=0):
    """
    Call ONLY after payment is confirmed.
    Creates digital download records and sends email with download links.
    max_downloads: 0 or None => unlimited
    """

    # Robust items access (related_name="items" OR default orderitem_set)
    items_manager = getattr(order, "items", None)
    items = items_manager.all() if items_manager is not None else order.orderitem_set.all()

    expires_at = None
    if days_valid and days_valid > 0:
        expires_at = timezone.now() + timedelta(days=days_valid)

    downloads = []
    for item in items:
        product = item.product

        is_digital = bool(getattr(product, "is_digital", False))
        has_file = bool(getattr(product, "digital_file", None))
        has_url = bool(getattr(product, "digital_url", None))

        if not is_digital or not (has_file or has_url):
            continue

        dl, _ = DigitalDownload.objects.get_or_create(
            order=order,
            product=product,
            defaults={
                "expires_at": expires_at,
                "max_downloads": max_downloads or 0,
            },
        )
        downloads.append(dl)

    if not downloads:
        return

    to_email = getattr(getattr(order, "user", None), "email", None)
    if not to_email:
        return

    # 1) Build the specific order page URL (this is what you want!)
    order_path = reverse("orders:my_order_detail", args=[order.id])

    # Optional: add a query param so you can highlight the downloads section
    order_path = f"{order_path}?highlight=downloads"

    # 2) Build a login URL that redirects to that order after login
    login_path = reverse("account_login")
    next_param = quote(order_path, safe="")  # safe="" so ? & = are encoded
    login_path_with_next = f"{login_path}?next={next_param}"

    # 3) Make absolute
    # Best: request.build_absolute_uri(...) because it matches the real domain/protocol
    order_url = request.build_absolute_uri(order_path)
    login_url = request.build_absolute_uri(login_path_with_next)

    subject = f"Your digital downloads for Order #{order.id}"
    message = (
        "Thanks for your purchase!\n\n"
        "Open your order to download your digital items:\n\n"
        f"{login_url}\n\n"
        "If you're already signed in, it will go directly to your order page.\n"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send digital download email for order #{order.id}: {e}")


def send_new_order_alert_emails(request, order):
    """
    Send "new order / product sold" alerts to:
    - Company (Support email from Company Settings)
    - Each seller whose products are in the order (seller's user email)
    Call only after payment is confirmed.
    """
    items_manager = getattr(order, "items", None)
    items = list(
        (items_manager.all() if items_manager else order.orderitem_set.all()).select_related(
            "seller", "seller__user", "product"
        )
    )
    if not items:
        return

    customer_email = getattr(getattr(order, "user", None), "email", None) or "Guest"
    order_total = getattr(order, "total", None)
    order_total_str = f"${float(order_total):.2f}" if order_total is not None else "N/A"

    # Build full order summary (for company and for per-seller messages)
    lines = []
    for item in items:
        product_name = getattr(item.product, "name", "Product")
        qty = getattr(item, "quantity", 0)
        price = getattr(item, "price", None) or getattr(item, "line_total", None)
        price_str = f"${float(price):.2f}" if price is not None else "N/A"
        seller_name = "—"
        if getattr(item, "seller", None):
            s = item.seller
            seller_name = getattr(s, "display_name", None) or getattr(getattr(s, "user", None), "email", None) or "Seller"
        lines.append(f"  • {product_name} x{qty} @ {price_str} (seller: {seller_name})")
    order_summary = "\n".join(lines)

    default_from = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")

    # 1) Company alert (Support email from Company Settings)
    try:
        from company_settings.models import CompanySettings
        company = CompanySettings.get_settings()
        support_email = getattr(company, "support_email", None) or getattr(company, "email", None)
        support_email = (support_email or "").strip()
        if support_email:
            subject = f"[New Order] Order #{order.id} – {order_total_str}"
            message = (
                f"A new order has been placed.\n\n"
                f"Order #: {order.id}\n"
                f"Total: {order_total_str}\n"
                f"Customer: {customer_email}\n\n"
                f"Items:\n{order_summary}\n"
            )
            send_mail(
                subject,
                message,
                default_from,
                [support_email],
                fail_silently=True,
            )
    except Exception as e:
        logger.warning("Could not send new-order alert to company: %s", e)

    # 2) Per-seller alerts (each seller gets only their items)
    seen_seller_ids = set()
    for item in items:
        seller = getattr(item, "seller", None)
        if not seller or (seller.id in seen_seller_ids):
            continue
        seen_seller_ids.add(seller.id)
        to_email = getattr(getattr(seller, "user", None), "email", None)
        if not to_email:
            continue
        seller_items = [i for i in items if getattr(i, "seller", None) and i.seller.id == seller.id]
        seller_lines = []
        seller_earnings_total = 0
        for i in seller_items:
            name = getattr(i.product, "name", "Product")
            qty = getattr(i, "quantity", 0)
            price = getattr(i, "price", None) or getattr(i, "line_total", None)
            price_str = f"${float(price):.2f}" if price is not None else "N/A"
            seller_lines.append(f"  • {name} x{qty} @ {price_str}")
            seller_earnings_total += float(getattr(i, "seller_earnings", 0) or 0)
        seller_summary = "\n".join(seller_lines)
        subject = f"[New Sale] Order #{order.id} – your items"
        message = (
            f"You have a new sale!\n\n"
            f"Order #: {order.id}\n"
            f"Your items:\n{seller_summary}\n\n"
            f"Your earnings for this order: ${seller_earnings_total:.2f}\n"
        )
        try:
            send_mail(
                subject,
                message,
                default_from,
                [to_email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning("Could not send new-order alert to seller %s: %s", seller.id, e)
