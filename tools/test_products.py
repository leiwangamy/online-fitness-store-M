"""
Quick script to test if products exist in database
Run: python test_products.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')
django.setup()

from products.models import Product, Category

def test_products():
    print("=" * 60)
    print("Testing Products in Database")
    print("=" * 60)
    
    # Count products
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    
    print(f"\nTotal products in database: {total_products}")
    print(f"Active products: {active_products}")
    
    if active_products == 0:
        print("\n⚠️  WARNING: No active products found!")
        print("\nTo add products:")
        print("1. Go to Django admin: http://127.0.0.1:8000/admin/")
        print("2. Navigate to Products > Products")
        print("3. Click 'Add Product'")
        print("4. Fill in the product details")
        print("5. Make sure 'Is active' is checked")
        print("6. Save the product")
    else:
        print(f"\n✅ Found {active_products} active product(s)")
        print("\nActive products:")
        for product in Product.objects.filter(is_active=True)[:10]:
            print(f"  - {product.name} (ID: {product.id}, Price: ${product.price})")
    
    # Count categories
    categories = Category.objects.count()
    print(f"\nTotal categories: {categories}")
    if categories > 0:
        print("Categories:")
        for cat in Category.objects.all():
            print(f"  - {cat.name} (slug: {cat.slug})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_products()

