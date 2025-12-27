# products/admin.py
from django.contrib import admin

from .forms import ProductAdminForm
from .models import Category, Product, ProductAudio, ProductImage, ProductVideo, InventoryLog


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductAudioInline(admin.TabularInline):
    model = ProductAudio
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin for all products (physical, digital, services).
    """
    form = ProductAdminForm

    csv_export_filename = "products.csv"
    csv_export_fields = ("id", "name", "price",  "product_type","availability_display")
    actions = ["export_as_csv"]
    

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "product_type",
        "availability_display",
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
    list_select_related = ("category",)
    inlines = [ProductImageInline, ProductVideoInline, ProductAudioInline]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "description", "price", "is_active", "category")}),
        ("Tax & Stock", {"fields": ("quantity_in_stock", "charge_gst", "charge_pst")}),
        ("Digital Product", {
            "fields": ("is_digital", "digital_file", "digital_url"),
            "classes": ("collapse",),
        }),
        ("Service Product", {
            "fields": (
                "is_service",
                "service_availability",
                "service_seats",
                "service_date",
                "service_time",
                "service_duration_minutes",
                "service_location",
            ),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Type")
    def product_type(self, obj: Product):
        if obj.is_digital:
            return "Digital"
        if obj.is_service:
            return "Service"
        return "Physical"

    @admin.display(description="Availability")
    def availability_display(self, obj: Product):
        return obj.availability_text

    class Media:
        js = ("js/product_admin.js",)


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "change_type", "delta", "order_id", "created_by", "created_at")
    list_filter = ("change_type", "created_at")
    search_fields = ("product__name", "=order_id", "note")
    date_hierarchy = "created_at"