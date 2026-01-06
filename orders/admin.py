# orders/admin.py
from django.contrib import admin
from decimal import Decimal
import csv
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Order, OrderItem, PickupLocation


# -------------------------
# CSV: Orders
# -------------------------
def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "Order ID", "User", "Status",
        "Subtotal", "Tax", "Shipping", "Total",
        "Created At",
    ])

    for order in queryset.select_related("user"):
        writer.writerow([
            order.id,
            str(order.user) if order.user else "",
            order.status,
            order.subtotal,
            order.tax,
            order.shipping,
            order.total,
            order.created_at,
        ])
    return response

export_orders_csv.short_description = "Export selected rows to CSV"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("line_total_admin",)
    fields = ("product", "quantity", "price", "line_total_admin")

    @admin.display(description="Line total")
    def line_total_admin(self, obj):
        qty = obj.quantity or 0
        price = obj.price if obj.price is not None else getattr(obj.product, "price", Decimal("0.00"))
        price = price or Decimal("0.00")
        return price * qty


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "status",
        "fulfillment_method_display", "pickup_location_display",
        "shipping_carrier", "tracking_number",
        "subtotal", "tax", "shipping", "total",
        "created_at",
    )
    list_display_links = ("id",)
    list_filter = ("status", "is_pickup", "shipping_carrier", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("=id", "user__username", "user__email", "tracking_number")
    inlines = (OrderItemInline,)
    actions = [export_orders_csv]

    readonly_fields = (
        "shipping_full_admin",
        "subtotal", "tax", "shipping", "total",
        "created_at", "updated_at",
    )

    fieldsets = (
        ("Order Info", {"fields": ("user", "status", "shipping_carrier", "tracking_number")}),
        ("Fulfillment Method", {"fields": ("is_pickup", "pickup_location")}),
        ("Shipping/Pickup Address", {"fields": (
            "ship_name", "ship_phone",
            "ship_address1", "ship_address2",
            "ship_city", "ship_province", "ship_postal_code", "ship_country",
            "shipping_full_admin",
        )}),
        ("Financial Summary", {"fields": ("subtotal", "tax", "shipping", "total")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Fulfillment", boolean=True)
    def fulfillment_method_display(self, obj):
        return "Pickup" if obj.is_pickup else "Shipping"
    fulfillment_method_display.short_description = "Method"

    @admin.display(description="Pickup Location")
    def pickup_location_display(self, obj):
        if obj.is_pickup and obj.pickup_location:
            return obj.pickup_location.name
        return "-"

    @admin.display(description="Shipping/Pickup Address")
    def shipping_full_admin(self, obj):
        if obj.is_pickup and obj.pickup_location:
            parts = [
                f"PICKUP: {obj.pickup_location.name}",
                obj.pickup_location.address1 or "",
                obj.pickup_location.address2 or "",
                " ".join([p for p in [obj.pickup_location.city or "", obj.pickup_location.province or "", obj.pickup_location.postal_code or ""] if p]).strip(),
                obj.pickup_location.country or "",
            ]
            if obj.pickup_location.phone:
                parts.insert(1, f"Phone: {obj.pickup_location.phone}")
            lines = [p.strip() for p in parts if p and p.strip()]
            return format_html("<br>".join(lines)) if lines else "-"
        
        parts = [
            obj.ship_name or "",
            obj.ship_phone or "",
            obj.ship_address1 or "",
            obj.ship_address2 or "",
            " ".join([p for p in [obj.ship_city or "", obj.ship_province or "", obj.ship_postal_code or ""] if p]).strip(),
            obj.ship_country or "",
        ]
        lines = [p.strip() for p in parts if p and p.strip()]
        return format_html("<br>".join(lines)) if lines else "-"


# -------------------------
# CSV: Order Items
# -------------------------
def export_orderitems_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="order_items.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "Order Status",
        "Order Created At",
        "User",
        "Product",
        "Qty",
        "Unit Price",
        "Line Total",
        "Is Digital",
        "Is Service",
    ])

    queryset = queryset.select_related("order", "order__user", "product")

    for item in queryset:
        product = item.product
        qty = item.quantity or 0
        price = item.price if item.price is not None else getattr(product, "price", Decimal("0.00"))
        price = price or Decimal("0.00")
        line_total = price * qty

        writer.writerow([
            item.order_id,
            item.order.status if item.order else "",
            item.order.created_at if item.order else "",
            str(item.order.user) if item.order and item.order.user else "",
            product.name if product else "",
            qty,
            price,
            line_total,
            bool(getattr(product, "is_digital", False)),
            bool(getattr(product, "is_service", False)),
        ])

    return response

export_orderitems_csv.short_description = "Export selected rows to CSV"


@admin.register(PickupLocation)
class PickupLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "province", "is_active", "display_order", "created_at")
    list_filter = ("is_active", "province", "city")
    search_fields = ("name", "address1", "city", "province", "postal_code")
    list_editable = ("is_active", "display_order")
    
    fieldsets = (
        ("Location Info", {"fields": ("name", "is_active", "display_order")}),
        ("Address", {"fields": (
            "address1", "address2",
            "city", "province", "postal_code", "country",
        )}),
        ("Contact & Instructions", {"fields": ("phone", "instructions")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    
    readonly_fields = ("created_at", "updated_at")


# ✅ One filter instead of two separate "By is ..."
class ItemTypeFilter(admin.SimpleListFilter):
    title = "Item type"
    parameter_name = "item_type"

    def lookups(self, request, model_admin):
        return (
            ("digital", "Digital"),
            ("service", "Service"),
            ("physical", "Physical"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "digital":
            return queryset.filter(product__is_digital=True)
        if v == "service":
            return queryset.filter(product__is_service=True)
        if v == "physical":
            return queryset.filter(product__is_digital=False, product__is_service=False)
        return queryset


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_id",
        "order_status",
        "product",
        "digital_flag",
        "service_flag",
        "quantity",
        "price",
        "line_total",
        "order_created_at",
    )
    list_filter = (
        "order__status",
        "order__created_at",
        ItemTypeFilter,   # ✅ better filter UI
    )
    search_fields = ("=order__id", "product__name", "order__user__username", "order__user__email")
    actions = [export_orderitems_csv]

    @admin.display(boolean=True, description="Digital")
    def digital_flag(self, obj):
        return bool(obj.product and getattr(obj.product, "is_digital", False))

    @admin.display(boolean=True, description="Service")
    def service_flag(self, obj):
        return bool(obj.product and getattr(obj.product, "is_service", False))

    @admin.display(description="Order status")
    def order_status(self, obj):
        return obj.order.status if obj.order else "-"

    @admin.display(description="Order created")
    def order_created_at(self, obj):
        return obj.order.created_at if obj.order else "-"

    @admin.display(description="Line total")
    def line_total(self, obj):
        qty = obj.quantity or 0
        price = obj.price or Decimal("0.00")
        return price * qty
