from django.contrib import admin
from .models import Product, ProductImage, ProductVideo, ProductAudio


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1


class ProductAudioInline(admin.TabularInline):
    model = ProductAudio
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [ProductImageInline, ProductVideoInline, ProductAudioInline]
