"""
API URLs - Central hub for all API endpoints

This module imports and registers all API viewsets from different apps.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

# Import viewsets from different apps
from products.api_views import ProductViewSet, CategoryViewSet

# Create a router and register all viewsets
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"categories", CategoryViewSet, basename="categories")

# Add more routers here as you add more API endpoints
# Example:
# from orders.api_views import OrderViewSet
# router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    
    # Authentication endpoint
    path("auth/token/", obtain_auth_token, name="api_token_auth"),
]

