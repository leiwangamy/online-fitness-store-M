# members/admin.py

from django.contrib import admin
from .models import Product, ProductImage, ProductVideo, ProductAudio, Category, Order, OrderItem, MemberProfile
from .forms import ProductAdminForm


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1


class ProductAudioInline(admin.TabularInline):
    model = ProductAudio
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin for all products (physical, digital, services).
    Uses ProductAdminForm to handle service_availability field.
    """
    form = ProductAdminForm

    # Columns in the product list page
    list_display = (
        "name",
        "category",
        "price",
        "product_type",          # Digital / Service / Physical
        "availability_display",  # Unlimited / seats / stock
        "charge_gst",
        "charge_pst",
        "is_active",
    )

    list_filter = (
        "category",
        "is_active",
        "charge_gst",
        "charge_pst",
        "is_digital",
        "is_service",
    )

    search_fields = ("name",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "description", "price", "is_active", "category"),
        }),
        ("Tax & Stock", {
            "fields": ("quantity_in_stock", "charge_gst", "charge_pst"),
        }),
        ("Digital Product", {
            "fields": ("is_digital",),
            "classes": ("collapse",),
        }),
        ("Service Product (Classes / Coaching)", {
            "fields": (
                "is_service",
                "service_availability",      # dropdown in the form
                "service_seats",             # only used when limited seats
                "service_date",
                "service_time",
                "service_duration_minutes",
                "service_location",
            ),
            "classes": ("collapse",),
        }),
    )

    inlines = [ProductImageInline, ProductVideoInline, ProductAudioInline]

    # ----- Helper fields for list_display -----

    def product_type(self, obj):
        if obj.is_digital:
            return "Digital"
        elif obj.is_service:
            return "Service"
        return "Physical"

    product_type.short_description = "Type"

    def availability_display(self, obj):
        # Digital: conceptually unlimited
        if obj.is_digital:
            return "Unlimited (digital)"

        # Service: seats or unlimited
        if obj.is_service:
            if obj.service_seats is None:
                return "Unlimited availability"
            return f"{obj.service_seats} seats"

        # Physical: quantity_in_stock
        qty = getattr(obj, "quantity_in_stock", None)
        if qty is None:
            return "N/A"
        return f"In stock: {qty}"

    availability_display.short_description = "Availability"

    # ----- Attach custom JS for dynamic admin behaviour -----

    class Media:
        # This file is at: members/static/members/js/product_admin.js
        js = ("members/js/product_admin.js",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "status",
        "shipping_carrier", "tracking_number",
        "total", "created_at",
    )
    list_display_links = ("id",)
    list_filter = ("status", "shipping_carrier", "created_at")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    readonly_fields = (
        "shipping_full",
        "subtotal", "tax", "shipping", "total",
        "created_at", "updated_at",
    )

    fieldsets = (
        ("Order Info", {
            "fields": ("user", "status", "shipping_carrier", "tracking_number")
        }),
        ("Shipping Address", {
            "fields": (
                "ship_name", "ship_phone",
                "ship_address1", "ship_address2",
                "ship_city", "ship_province", "ship_postal_code", "ship_country",
                "shipping_full",
            )
        }),
        ("Financial Summary", {
            "fields": ("subtotal", "tax", "shipping", "total")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "membership_level",
        "is_member",
        "is_active_member_display",
        "membership_started",
        "membership_expires",
        "auto_renew",
        "next_billing_date",
    )

    list_filter = (
        "membership_level",
        "is_member",
        "auto_renew",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "membership_started",
        "membership_expires",
    )

    def is_active_member_display(self, obj):
        return obj.is_active_member
    is_active_member_display.boolean = True
    is_active_member_display.short_description = "Active now?"

