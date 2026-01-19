"""
URLs for seller application and dashboard
"""
from django.urls import path
from . import views

app_name = "sellers"

urlpatterns = [
    # Seller application (public for logged-in users)
    path("apply/", views.apply, name="apply"),
    path("application-status/", views.application_status, name="application_status"),
    
    # Seller dashboard (approved sellers only)
    path("dashboard/", views.dashboard, name="dashboard"),
    
    # Product management (approved sellers only)
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    
    # Order management (approved sellers only)
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/refund/<int:order_item_id>/", views.refund_order_item, name="refund_order_item"),
    
    # Earnings statement (approved sellers only)
    path("earnings/statement/", views.earnings_statement, name="earnings_statement"),
    
    # Data export (approved sellers only)
    path("data-export/", views.data_export, name="data_export"),
]

