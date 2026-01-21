"""
Product API Views

API endpoints for Product model using Django REST Framework ViewSets.
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Category model.
    Public access - no authentication required.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Product model.
    
    Endpoints:
    - GET /api/products/ - List all active products
    - GET /api/products/{id}/ - Get product details
    - GET /api/products/featured/ - Get featured products
    - GET /api/products/search/?q=query - Search products
    
    Public access for reading, but can be restricted if needed.
    """
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Return only active products by default.
        Can be filtered by category, seller, or search query.
        """
        queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'seller', 'seller__user'
        ).prefetch_related('images')
        
        # Filter by category if provided
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by seller if provided
        seller_id = self.request.query_params.get('seller', None)
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        
        # Filter by product type
        is_digital = self.request.query_params.get('is_digital', None)
        if is_digital is not None:
            queryset = queryset.filter(is_digital=is_digital.lower() == 'true')
        
        is_service = self.request.query_params.get('is_service', None)
        if is_service is not None:
            queryset = queryset.filter(is_service=is_service.lower() == 'true')
        
        # Search by name or description
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter featured products
        featured_only = self.request.query_params.get('featured', None)
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Order by featured first, then by ID (newest first)
        return queryset.order_by('-is_featured', '-id')
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Custom endpoint to get featured products.
        GET /api/products/featured/
        """
        featured_products = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Custom endpoint for product search.
        GET /api/products/search/?q=query
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)
        
        products = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            "query": query,
            "count": products.count(),
            "results": serializer.data
        })

