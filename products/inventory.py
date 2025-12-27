# products/inventory.py
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from .models import InventoryLog

@transaction.atomic
def set_beginning_balance(*, product, quantity: int, user=None, note="Beginning balance"):
    """
    Sets product stock to 'quantity' and writes ONE immutable log row.
    Use this to set the initial inventory balance for a product.
    """
    # Update the product's quantity_in_stock field
    product.quantity_in_stock = quantity
    product.save(update_fields=["quantity_in_stock"])

    # Create a log entry for the beginning balance
    InventoryLog.objects.create(
        product=product,
        change_type=InventoryLog.ChangeType.INITIAL,
        delta=quantity,
        created_by=user,
        note=note,
    )

@transaction.atomic
def adjust_inventory(*, product, delta: int, change_type: str, created_by=None, order=None, note=""):
    """
    delta: negative reduces stock, positive adds stock
    Updates stock and creates a log entry.
    """
    # Update stock safely in DB (no race conditions)
    # Use quantity_in_stock field (not stock)
    # Use Greatest to ensure stock never goes below 0
    product.__class__.objects.filter(pk=product.pk).update(
        quantity_in_stock=Greatest(0, F("quantity_in_stock") + delta)
    )
    
    # Refresh the product instance to get updated value
    product.refresh_from_db()

    # Create a log row
    InventoryLog.objects.create(
        product=product,
        delta=delta,
        change_type=change_type,
        created_by=created_by,
        order_id=getattr(order, "id", None),
        note=note,
    )


def log_purchase(*, product, quantity: int, change_type: str, created_by=None, order=None, note=""):
    """
    Log a purchase without updating stock (for digital products, services, etc.).
    This creates an inventory log entry with delta=0 or negative quantity for tracking.
    """
    InventoryLog.objects.create(
        product=product,
        delta=-quantity,  # Negative to show it was purchased (even though stock doesn't change)
        change_type=change_type,
        created_by=created_by,
        order_id=getattr(order, "id", None),
        note=note,
    )
