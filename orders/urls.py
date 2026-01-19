from django.urls import path

from . import views_orders, views_downloads, admin_views

app_name = "orders"

urlpatterns = [
    path("my-orders/", views_orders.my_orders, name="my_orders"),
    path("my_orders_detail/<int:order_id>/", views_orders.my_order_detail, name="my_order_detail"),
    path("download/<uuid:token>/", views_downloads.digital_download, name="digital_download"),
    
    # Admin refund management
    path("admin/refunds/", admin_views.admin_refund_queue, name="admin_refund_queue"),
    path("admin/refunds/<int:refund_id>/approve/", admin_views.admin_approve_refund, name="admin_approve_refund"),
    path("admin/refunds/<int:refund_id>/reject/", admin_views.admin_reject_refund, name="admin_reject_refund"),
]
