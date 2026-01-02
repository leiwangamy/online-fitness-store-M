from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import DigitalDownload


def create_downloads_and_email(request, order, days_valid=7, max_downloads=0):
    """
    Call ONLY after payment is confirmed.
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

    links = []
    for dl in downloads:
        path = reverse("orders:digital_download", args=[str(dl.token)])
        # Use Site framework to get the correct domain (includes port :8000)
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        # Build URL with site domain (which includes :8000)
        if site.domain:
            # site.domain should be like "ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000"
            protocol = 'https' if request.is_secure() else 'http'
            url = f"{protocol}://{site.domain}{path}"
        else:
            # Fallback to request.build_absolute_uri if site domain not set
            url = request.build_absolute_uri(path)
        links.append(f"{dl.product.name}: {url}")

    to_email = getattr(getattr(order, "user", None), "email", None)
    if not to_email:
        return

    subject = f"Your digital downloads for Order #{order.id}"
    message = (
        "Thanks for your purchase!\n\n"
        "Here are your download links:\n\n"
        + "\n".join(links)
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )
