"""
Product API Serializers

Serializers convert Product model instances to/from JSON for API responses.
"""

from rest_framework import serializers
from .models import Product, Category, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url", "is_main", "alt_text"]
    
    def get_image_url(self, obj):
        """Return full URL for the image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    seller_name = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    digital_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "is_active",
            "is_featured",
            "quantity_in_stock",
            "charge_gst",
            "charge_pst",
            "is_digital",
            "is_service",
            "digital_file",
            "digital_file_url",
            "digital_url",
            "service_seats",
            "service_date",
            "service_time",
            "service_location",
            "category",
            "category_id",
            "seller",
            "seller_name",
            "images",
            "main_image_url",
        ]
        read_only_fields = ["seller"]
    
    def get_seller_name(self, obj):
        """Return seller's display name or username"""
        if obj.seller:
            return obj.seller.display_name or obj.seller.user.username
        return None
    
    def get_main_image_url(self, obj):
        """Return URL of the main product image"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None
    
    def get_digital_file_url(self, obj):
        """Return full URL for digital file if exists"""
        if obj.digital_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.digital_file.url)
            return obj.digital_file.url
        return None

