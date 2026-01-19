# orders/admin.py
from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html
from decimal import Decimal
import csv
from django.http import HttpResponse

from .models import Order, OrderItem, PickupLocation, Refund
try:
    from services.stripe_refunds import create_stripe_refund, StripeRefundError, _to_cents
except ImportError:
    # Handle case where stripe package is not installed
    create_stripe_refund = None
    StripeRefundError = Exception
    _to_cents = None


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
    autocomplete_fields = ("product", "seller")
    readonly_fields = ("line_total_admin", "platform_fee", "seller_earnings")
    fields = ("product", "seller", "quantity", "price", "line_total_admin", "platform_fee", "seller_earnings")

    @admin.display(description="Line total")
    def line_total_admin(self, obj):
        qty = obj.quantity or 0
        price = obj.price if obj.price is not None else getattr(obj.product, "price", Decimal("0.00"))
        price = price or Decimal("0.00")
        return price * qty


class RefundInline(admin.TabularInline):
    """
    Inline admin for displaying refunds in Order admin page.
    Read-only display of seller refund requests with action dropdown.
    """
    model = Refund
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        # No adding through inline - use Force Refund button instead
        return False
    
    readonly_fields = (
        "refund_display", "amount", "reason", "status_display",
        "created_by_display", "created_at", "stripe_refund_id", "refund_action_dropdown"
    )
    fields = (
        "refund_display", "amount", "reason", "status_display",
        "created_by_display", "created_at", "stripe_refund_id", "refund_action_dropdown"
    )
    
    @admin.display(description="Refund")
    def refund_display(self, obj):
        """Display refund info with product name if available"""
        if obj.order_item and obj.order_item.product:
            product_name = obj.order_item.product.name
            seller_name = obj.seller.display_name or obj.seller.user.email
            return format_html(
                '<strong>{}</strong> – {} – <strong>${}</strong>',
                product_name,
                seller_name,
                obj.amount
            )
        return format_html(
            '<strong>Full Order Refund</strong> – {} – <strong>${}</strong>',
            obj.seller.display_name or obj.seller.user.email,
            obj.amount
        )
    
    @admin.display(description="Status")
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            Refund.STATUS_REQUESTED: '#fff3cd',
            Refund.STATUS_APPROVED: '#d1ecf1',
            Refund.STATUS_REJECTED: '#f8d7da',
            Refund.STATUS_PROCESSING: '#cce5ff',
            Refund.STATUS_SUCCEEDED: '#d4edda',
            Refund.STATUS_FAILED: '#f8d7da',
        }
        color = status_colors.get(obj.status, '#f0f0f0')
        return format_html(
            '<span style="background: {}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description="Created By")
    def created_by_display(self, obj):
        """Display who created the refund"""
        return obj.created_by.get_full_name() or obj.created_by.email
    
    @admin.display(description="Action")
    def refund_action_dropdown(self, obj):
        """Display dropdown for approve/reject/force refund actions"""
        from django.urls import reverse
        approve_url = reverse('admin:orders_refund_approve', args=[obj.order.id, obj.id])
        reject_url = reverse('admin:orders_refund_reject', args=[obj.order.id, obj.id])
        force_url = reverse('admin:orders_force_refund', args=[obj.order.id])
        
        if obj.status == Refund.STATUS_REQUESTED:
            return format_html(
                '<select onchange="if(this.value) {{ window.location.href=this.value; }}" style="padding: 5px; border-radius: 3px; min-width: 150px;">'
                '<option value="">-- Select Action --</option>'
                '<option value="{}" style="color: #28a745;">✓ Approve Refund</option>'
                '<option value="{}" style="color: #dc3545;">✗ Reject</option>'
                '<option value="{}" style="color: #ff9800;">⚡ Force Refund (Override)</option>'
                '</select>',
                approve_url,
                reject_url,
                force_url
            )
        elif obj.status in [Refund.STATUS_APPROVED, Refund.STATUS_PROCESSING]:
            return format_html('<span style="color: #856404;">Processing...</span>')
        elif obj.status == Refund.STATUS_SUCCEEDED:
            return format_html('<span style="color: #28a745;">✓ Completed</span>')
        elif obj.status == Refund.STATUS_REJECTED:
            return format_html('<span style="color: #dc3545;">✗ Rejected</span>')
        elif obj.status == Refund.STATUS_FAILED:
            return format_html('<span style="color: #dc3545;">⚠ Failed</span>')
        else:
            return format_html(
                '<select onchange="if(this.value) {{ window.location.href=this.value; }}" style="padding: 5px; border-radius: 3px; min-width: 150px;">'
                '<option value="">-- Select Action --</option>'
                '<option value="{}" style="color: #ff9800;">⚡ Force Refund (Override)</option>'
                '</select>',
                force_url
            )
    
    class Media:
        css = {
            'all': ('admin/css/refund_inline.css',)
        }


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "status",
        "fulfillment_method_display", "pickup_location_display",
        "shipping_carrier", "tracking_number",
        "payment_intent_id",
        "subtotal", "tax", "shipping", "total",
        "created_at",
    )
    list_display_links = ("id",)
    list_filter = ("status", "is_pickup", "shipping_carrier", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("=id", "user__username", "user__email", "tracking_number")
    inlines = (OrderItemInline, RefundInline)
    actions = [export_orders_csv]
    list_select_related = ("user", "pickup_location")
    
    def get_queryset(self, request):
        """Optimize queryset for list view"""
        qs = super().get_queryset(request)
        return qs.select_related("user", "pickup_location").prefetch_related("refunds", "refunds__seller", "refunds__order_item")
    
    def get_urls(self):
        """Add custom URLs for refund actions"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:order_id>/refund/<int:refund_id>/approve/',
                self.admin_site.admin_view(self.approve_refund),
                name='orders_refund_approve',
            ),
            path(
                '<int:order_id>/refund/<int:refund_id>/reject/',
                self.admin_site.admin_view(self.reject_refund),
                name='orders_refund_reject',
            ),
            path(
                '<int:order_id>/force-refund/',
                self.admin_site.admin_view(self.force_refund),
                name='orders_force_refund',
            ),
        ]
        return custom_urls + urls
    
    @transaction.atomic
    def approve_refund(self, request, order_id, refund_id):
        """Admin action to approve and process a refund"""
        order = get_object_or_404(Order, id=order_id)
        refund = get_object_or_404(Refund, id=refund_id, order=order, status=Refund.STATUS_REQUESTED)
        
        if not order.payment_intent_id:
            messages.error(request, "Order missing Stripe payment reference. Cannot process refund.")
            return redirect('admin:orders_order_change', order_id)
        
        # Update refund status to processing
        refund.status = Refund.STATUS_PROCESSING
        refund.save(update_fields=["status"])
        
        try:
            # Process Stripe refund
            stripe_refund_id = create_stripe_refund(
                payment_intent_id=order.payment_intent_id,
                amount_cents=_to_cents(refund.amount),
                reason="requested_by_customer"
            )
            
            # Update refund with Stripe ID and mark as succeeded
            refund.stripe_refund_id = stripe_refund_id
            refund.status = Refund.STATUS_SUCCEEDED
            refund.save(update_fields=["stripe_refund_id", "status"])
            
            # Update order status
            from django.db.models import Sum
            total_refunded = Refund.objects.filter(
                order=order,
                status=Refund.STATUS_SUCCEEDED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            if total_refunded >= order.total:
                order.status = Order.STATUS_REFUNDED
            else:
                order.status = Order.STATUS_PARTIALLY_REFUNDED
            order.save(update_fields=["status"])
            
            messages.success(request, f"Refund #{refund.id} approved and processed successfully via Stripe.")
        except StripeRefundError as e:
            refund.status = Refund.STATUS_FAILED
            refund.save(update_fields=["status"])
            messages.error(request, f"Stripe refund failed: {str(e)}")
        except Exception as e:
            refund.status = Refund.STATUS_FAILED
            refund.save(update_fields=["status"])
            messages.error(request, f"An error occurred: {str(e)}")
        
        return redirect('admin:orders_order_change', order_id)
    
    @transaction.atomic
    def reject_refund(self, request, order_id, refund_id):
        """Admin action to reject a refund request"""
        order = get_object_or_404(Order, id=order_id)
        refund = get_object_or_404(Refund, id=refund_id, order=order, status=Refund.STATUS_REQUESTED)
        
        refund.status = Refund.STATUS_REJECTED
        refund.save(update_fields=["status"])
        
        messages.info(request, f"Refund request #{refund.id} has been rejected.")
        return redirect('admin:orders_order_change', order_id)
    
    def force_refund(self, request, order_id):
        """Admin action to create a refund (admin override)"""
        from django.forms import ModelForm
        from django.shortcuts import render
        
        order = get_object_or_404(Order, id=order_id)
        
        class ForceRefundForm(ModelForm):
            class Meta:
                model = Refund
                fields = ['order_item', 'seller', 'amount', 'reason']
                widgets = {
                    'reason': admin.widgets.AdminTextareaWidget(attrs={'rows': 3}),
                }
        
        if request.method == 'POST':
            form = ForceRefundForm(request.POST)
            if form.is_valid():
                refund = form.save(commit=False)
                refund.order = order
                refund.created_by = request.user
                refund.status = Refund.STATUS_APPROVED  # Auto-approve admin-created refunds
                refund.save()
                
                # Process immediately
                if order.payment_intent_id:
                    try:
                        refund.status = Refund.STATUS_PROCESSING
                        refund.save(update_fields=["status"])
                        
                        if not create_stripe_refund or not _to_cents:
                            raise Exception("Stripe refund service is not available. Please install stripe package.")
                        stripe_refund_id = create_stripe_refund(
                            payment_intent_id=order.payment_intent_id,
                            amount_cents=_to_cents(refund.amount),
                            reason="admin_override"
                        )
                        
                        refund.stripe_refund_id = stripe_refund_id
                        refund.status = Refund.STATUS_SUCCEEDED
                        refund.save(update_fields=["stripe_refund_id", "status"])
                        
                        # Update order status
                        from django.db.models import Sum
                        total_refunded = Refund.objects.filter(
                            order=order,
                            status=Refund.STATUS_SUCCEEDED
                        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                        
                        if total_refunded >= order.total:
                            order.status = Order.STATUS_REFUNDED
                        else:
                            order.status = Order.STATUS_PARTIALLY_REFUNDED
                        order.save(update_fields=["status"])
                        
                        messages.success(request, f"Refund created and processed successfully.")
                    except Exception as e:
                        refund.status = Refund.STATUS_FAILED
                        refund.save(update_fields=["status"])
                        messages.error(request, f"Refund creation failed: {str(e)}")
                else:
                    messages.warning(request, "Order missing Stripe payment reference. Refund created but not processed.")
                
                return redirect('admin:orders_order_change', order_id)
        else:
            form = ForceRefundForm(initial={'order': order})
            # Limit order_item and seller to this order
            form.fields['order_item'].queryset = OrderItem.objects.filter(order=order)
            form.fields['seller'].queryset = order.items.values_list('seller', flat=True).distinct()
        
        return render(request, 'admin/orders/force_refund.html', {
            'order': order,
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, order),
        })

    readonly_fields = (
        "shipping_full_admin",
        "subtotal", "tax", "shipping", "total",
        "created_at", "updated_at",
        "force_refund_link",
    )

    fieldsets = (
        ("Order Info", {"fields": ("user", "status", "payment_intent_id", "shipping_carrier", "tracking_number")}),
        ("Fulfillment Method", {"fields": ("is_pickup", "pickup_location")}),
        ("Shipping/Pickup Address", {"fields": (
            "ship_name", "ship_phone",
            "ship_address1", "ship_address2",
            "ship_city", "ship_province", "ship_postal_code", "ship_country",
            "shipping_full_admin",
        )}),
        ("Financial Summary", {"fields": ("subtotal", "tax", "shipping", "total")}),
        ("Admin Actions", {
            "fields": ("force_refund_link",),
            "description": "Admin override: Create refunds even if seller has not requested them."
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    
    @admin.display(description="Force Refund")
    def force_refund_link(self, obj):
        """Link to create a refund (admin override)"""
        if obj and obj.id:
            url = reverse('admin:orders_force_refund', args=[obj.id])
            return format_html(
                '<a href="{}" class="button" style="background: #ff9800; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold;">Force Refund</a>',
                url
            )
        return "-"

    @admin.display(description="Fulfillment")
    def fulfillment_method_display(self, obj):
        """Display fulfillment method safely"""
        if obj is None:
            return "-"
        try:
            is_pickup = getattr(obj, 'is_pickup', False)
            return "Pickup" if is_pickup else "Shipping"
        except (AttributeError, Exception):
            return "Shipping"

    @admin.display(description="Pickup Location")
    def pickup_location_display(self, obj):
        """Display pickup location safely"""
        if obj is None:
            return "-"
        try:
            is_pickup = getattr(obj, 'is_pickup', False)
            if not is_pickup:
                return "-"
            
            if not hasattr(obj, 'pickup_location'):
                return "-"
            
            pickup_location = getattr(obj, 'pickup_location', None)
            if pickup_location is None:
                return "-"
            
            # Safely get the name
            if hasattr(pickup_location, 'name'):
                return str(pickup_location.name)
            return "-"
        except (AttributeError, Exception) as e:
            # Log error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error displaying pickup location for order {obj.id if obj else 'unknown'}: {e}")
            return "-"

    @admin.display(description="Shipping/Pickup Address")
    def shipping_full_admin(self, obj):
        try:
            is_pickup = getattr(obj, 'is_pickup', False)
            if is_pickup and hasattr(obj, 'pickup_location') and obj.pickup_location:
                try:
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
                except Exception:
                    pass
        except Exception:
            pass
        
        # Fallback to shipping address
        try:
            parts = [
                getattr(obj, 'ship_name', '') or "",
                getattr(obj, 'ship_phone', '') or "",
                getattr(obj, 'ship_address1', '') or "",
                getattr(obj, 'ship_address2', '') or "",
                " ".join([p for p in [getattr(obj, 'ship_city', '') or "", getattr(obj, 'ship_province', '') or "", getattr(obj, 'ship_postal_code', '') or ""] if p]).strip(),
                getattr(obj, 'ship_country', '') or "",
            ]
            lines = [p.strip() for p in parts if p and p.strip()]
            return format_html("<br>".join(lines)) if lines else "-"
        except Exception:
            return "-"


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
        "Seller",
        "Qty",
        "Unit Price",
        "Line Total",
        "Platform Fee",
        "Seller Earnings",
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
            str(item.seller) if item.seller else "",
            qty,
            price,
            item.line_total if item.line_total else line_total,
            item.platform_fee if item.platform_fee else Decimal("0.00"),
            item.seller_earnings if item.seller_earnings else Decimal("0.00"),
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
        "seller",
        "digital_flag",
        "service_flag",
        "quantity",
        "price",
        "line_total",
        "platform_fee",
        "seller_earnings",
        "order_created_at",
    )
    list_filter = (
        "order__status",
        "seller",
        "order__created_at",
        ItemTypeFilter,   # ✅ better filter UI
    )
    search_fields = ("=order__id", "product__name", "seller__display_name", "seller__user__email", "order__user__username", "order__user__email")
    list_select_related = ("order", "product", "seller", "seller__user")
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
        # Use stored field if available, otherwise calculate
        if obj.line_total and obj.line_total > Decimal("0.00"):
            return obj.line_total
        qty = obj.quantity or 0
        price = obj.price or Decimal("0.00")
        return price * qty


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """
    Admin interface for managing refund requests.
    Default view shows only requested refunds for quick admin access.
    """
    list_display = (
        "id", "order_link", "order_item_display", "seller_display",
        "amount", "status_display", "created_by_display", "created_at"
    )
    list_filter = ("status", "created_at", "seller")
    search_fields = ("=id", "=order__id", "seller__display_name", "seller__user__email", "order__user__email")
    list_select_related = ("order", "order_item", "seller", "seller__user", "created_by")
    date_hierarchy = "created_at"
    readonly_fields = (
        "order", "order_item", "seller", "amount", "reason",
        "created_by", "status", "created_at", "stripe_refund_id"
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related("order", "order_item", "seller", "seller__user", "created_by")
    
    def changelist_view(self, request, extra_context=None):
        """Override to default filter to requested refunds"""
        if 'status__exact' not in request.GET:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            url = reverse('admin:orders_refund_changelist')
            return HttpResponseRedirect(f"{url}?status__exact={Refund.STATUS_REQUESTED}")
        return super().changelist_view(request, extra_context)
    
    @admin.display(description="Order")
    def order_link(self, obj):
        """Link to order admin page"""
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
        return "-"
    order_link.admin_order_field = "order__id"
    
    @admin.display(description="Order Item")
    def order_item_display(self, obj):
        """Display order item product name"""
        if obj.order_item and obj.order_item.product:
            return obj.order_item.product.name
        return "Full Order Refund"
    
    @admin.display(description="Seller")
    def seller_display(self, obj):
        """Display seller name"""
        if obj.seller:
            return obj.seller.display_name or obj.seller.user.email
        return "-"
    seller_display.admin_order_field = "seller__display_name"
    
    @admin.display(description="Status")
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            Refund.STATUS_REQUESTED: '#fff3cd',
            Refund.STATUS_APPROVED: '#d1ecf1',
            Refund.STATUS_REJECTED: '#f8d7da',
            Refund.STATUS_PROCESSING: '#cce5ff',
            Refund.STATUS_SUCCEEDED: '#d4edda',
            Refund.STATUS_FAILED: '#f8d7da',
        }
        color = status_colors.get(obj.status, '#f0f0f0')
        return format_html(
            '<span style="background: {}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.admin_order_field = "status"
    
    @admin.display(description="Created By")
    def created_by_display(self, obj):
        """Display who created the refund"""
        return obj.created_by.get_full_name() or obj.created_by.email
    created_by_display.admin_order_field = "created_by__email"
    
    fieldsets = (
        ("Refund Information", {
            "fields": ("order", "order_item", "seller", "amount", "reason")
        }),
        ("Status & Processing", {
            "fields": ("status", "stripe_refund_id", "created_by", "created_at")
        }),
    )
    
    actions = ['approve_selected_refunds', 'reject_selected_refunds']
    
    @admin.action(description="Approve and process selected refunds")
    @transaction.atomic
    def approve_selected_refunds(self, request, queryset):
        """Bulk approve refunds"""
        approved = 0
        failed = 0
        for refund in queryset.filter(status=Refund.STATUS_REQUESTED):
            try:
                order = refund.order
                if not order.payment_intent_id:
                    continue
                
                refund.status = Refund.STATUS_PROCESSING
                refund.save(update_fields=["status"])
                
                if create_stripe_refund and _to_cents:
                    stripe_refund_id = create_stripe_refund(
                        payment_intent_id=order.payment_intent_id,
                        amount_cents=_to_cents(refund.amount),
                        reason="requested_by_customer"
                    )
                    refund.stripe_refund_id = stripe_refund_id
                    refund.status = Refund.STATUS_SUCCEEDED
                    refund.save(update_fields=["stripe_refund_id", "status"])
                    
                    from django.db.models import Sum
                    total_refunded = Refund.objects.filter(
                        order=order,
                        status=Refund.STATUS_SUCCEEDED
                    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                    
                    if total_refunded >= order.total:
                        order.status = Order.STATUS_REFUNDED
                    else:
                        order.status = Order.STATUS_PARTIALLY_REFUNDED
                    order.save(update_fields=["status"])
                    
                    approved += 1
                else:
                    refund.status = Refund.STATUS_FAILED
                    refund.save(update_fields=["status"])
                    failed += 1
            except Exception:
                refund.status = Refund.STATUS_FAILED
                refund.save(update_fields=["status"])
                failed += 1
        
        if approved > 0:
            self.message_user(request, f"{approved} refund(s) approved and processed successfully.")
        if failed > 0:
            self.message_user(request, f"{failed} refund(s) failed to process.", level=messages.WARNING)
    
    @admin.action(description="Reject selected refund requests")
    def reject_selected_refunds(self, request, queryset):
        """Bulk reject refunds"""
        updated = queryset.filter(status=Refund.STATUS_REQUESTED).update(status=Refund.STATUS_REJECTED)
        self.message_user(request, f"{updated} refund request(s) rejected.")

