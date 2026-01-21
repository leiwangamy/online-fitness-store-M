"""
Product API URLs

API routing for Product and Category endpoints using DRF routers.
"""

from rest_framework.routers import DefaultRouter
from .api_views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"categories", CategoryViewSet, basename="categories")

urlpatterns = router.urls

