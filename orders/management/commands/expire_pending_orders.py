"""
Django management command to expire pending orders after 30 minutes.

This command:
1. Finds orders with status="pending" older than 30 minutes
2. Releases reserved inventory back to products
3. Cancels expired orders (or marks them for cleanup)

Usage:
    python manage.py expire_pending_orders

This should be run periodically (e.g., every 5-10 minutes) via cron or scheduled task.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order


class Command(BaseCommand):
    help = 'Expire pending orders older than 30 minutes and release reserved inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Minutes after which pending orders expire (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually expiring orders',
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        dry_run = options['dry_run']
        expiry_time = timezone.now() - timedelta(minutes=minutes)

        # Find pending orders older than expiry_time
        expired_orders = Order.objects.filter(
            status=Order.STATUS_PENDING,
            created_at__lt=expiry_time
        ).select_related('user').prefetch_related('items__product')

        count = expired_orders.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No pending orders older than {minutes} minutes found.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Found {count} pending order(s) older than {minutes} minutes.')
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No orders will be expired.'))
            for order in expired_orders:
                self.stdout.write(f'  - Order #{order.id} (created: {order.created_at})')
            return

        # Process expired orders
        expired_count = 0
        inventory_released = 0

        for order in expired_orders:
            try:
                with transaction.atomic():
                    # Release inventory for each order item
                    for item in order.items.all():
                        product = item.product
                        qty = item.quantity

                        is_digital = bool(getattr(product, "is_digital", False))
                        is_service = bool(getattr(product, "is_service", False))

                        if is_digital:
                            # Digital products don't have inventory to release
                            continue

                        if is_service:
                            # Release service seats back
                            seats = getattr(product, "service_seats", None)
                            if seats is not None:
                                product.refresh_from_db()
                                product.service_seats = getattr(product, "service_seats", 0) + qty
                                product.save(update_fields=["service_seats"])
                                inventory_released += 1
                        else:
                            # Release physical product inventory back
                            stock = getattr(product, "quantity_in_stock", None)
                            if stock is not None:
                                from products.inventory import adjust_inventory
                                adjust_inventory(
                                    product=product,
                                    delta=+qty,  # Positive to add stock back
                                    change_type="ORDER",  # Using ORDER type with note explaining expiration
                                    order=order,
                                    note=f"Order #{order.id} EXPIRED - Released {qty} units back to inventory"
                                )
                                inventory_released += 1

                    # Mark order as cancelled
                    order.status = Order.STATUS_CANCELLED
                    order.save(update_fields=['status'])
                    expired_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Expired Order #{order.id} - Released inventory for {order.items.count()} item(s)'
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to expire Order #{order.id}: {str(e)}')
                )
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to expire Order #{order.id}: {e}', exc_info=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nExpired {expired_count} order(s) and released inventory for {inventory_released} product(s).'
            )
        )

