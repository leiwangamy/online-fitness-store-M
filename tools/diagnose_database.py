"""
Comprehensive database diagnostic script
Run: python diagnose_database.py
"""
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')

import django
django.setup()

from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.db.utils import OperationalError

def check_database():
    print("=" * 70)
    print("DATABASE DIAGNOSTIC REPORT")
    print("=" * 70)
    
    # 1. Check database configuration
    db_config = settings.DATABASES['default']
    print(f"\n1. DATABASE CONFIGURATION:")
    print(f"   Engine: {db_config['ENGINE']}")
    print(f"   Database Name: {db_config['NAME']}")
    print(f"   User: {db_config['USER']}")
    print(f"   Host: {db_config['HOST']}")
    print(f"   Port: {db_config['PORT']}")
    
    # 2. Test connection
    print(f"\n2. CONNECTION TEST:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   ✅ Connected to PostgreSQL")
            print(f"   Version: {version.split(',')[0]}")
            
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"   Current database: {db_name}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"\n   ACTION REQUIRED: Fix database connection first!")
        return False
    
    # 3. Check if tables exist
    print(f"\n3. CHECKING TABLES:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if tables:
                print(f"   ✅ Found {len(tables)} tables in database")
                print(f"   Tables: {', '.join(tables[:10])}")
                if len(tables) > 10:
                    print(f"   ... and {len(tables) - 10} more")
            else:
                print(f"   ⚠️  No tables found in database!")
                print(f"   ACTION REQUIRED: Run migrations!")
                return False
    except Exception as e:
        print(f"   ❌ Error checking tables: {e}")
        return False
    
    # 4. Check if products table exists and has data
    print(f"\n4. CHECKING PRODUCTS TABLE:")
    try:
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'products_product'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print(f"   ❌ Products table does not exist!")
                print(f"   ACTION REQUIRED: Run migrations!")
                return False
            
            print(f"   ✅ Products table exists")
            
            # Count products
            cursor.execute("SELECT COUNT(*) FROM products_product;")
            total_count = cursor.fetchone()[0]
            print(f"   Total products: {total_count}")
            
            # Count active products
            cursor.execute("SELECT COUNT(*) FROM products_product WHERE is_active = TRUE;")
            active_count = cursor.fetchone()[0]
            print(f"   Active products: {active_count}")
            
            if total_count == 0:
                print(f"\n   ⚠️  WARNING: No products in database!")
                print(f"   ACTION REQUIRED: Add products via Django admin or import data")
            elif active_count == 0:
                print(f"\n   ⚠️  WARNING: Products exist but none are active!")
                print(f"   ACTION REQUIRED: Check 'is_active' field in admin")
            
            # Show sample products
            if total_count > 0:
                cursor.execute("""
                    SELECT id, name, is_active, price 
                    FROM products_product 
                    ORDER BY id 
                    LIMIT 5;
                """)
                print(f"\n   Sample products:")
                for row in cursor.fetchall():
                    status = "✅ Active" if row[2] else "❌ Inactive"
                    print(f"     - ID {row[0]}: {row[1]} ({status}) - ${row[3]}")
    
    except Exception as e:
        print(f"   ❌ Error checking products: {e}")
        return False
    
    # 5. Check migrations status
    print(f"\n5. MIGRATION STATUS:")
    try:
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()
        print(f"   Applied migrations: {len(applied)}")
        
        # Check if products migrations are applied
        products_migrations = [m for m in applied if m[0] == 'products']
        if products_migrations:
            print(f"   ✅ Products app migrations applied: {len(products_migrations)}")
        else:
            print(f"   ⚠️  No products migrations found!")
            print(f"   ACTION REQUIRED: Run 'python manage.py migrate products'")
    except Exception as e:
        print(f"   ⚠️  Could not check migrations: {e}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    
    if total_count == 0:
        print("1. Your database is connected and working ✅")
        print("2. Tables exist ✅")
        print("3. But you have NO products in the database ❌")
        print("\n   NEXT STEPS:")
        print("   - Go to Django admin: http://127.0.0.1:8000/admin/")
        print("   - Navigate to Products > Products")
        print("   - Click 'Add Product' to create new products")
        print("   - Make sure 'Is active' checkbox is checked")
    elif active_count == 0:
        print("1. Your database is connected ✅")
        print("2. Products exist in database ✅")
        print("3. But NO products are marked as active ❌")
        print("\n   NEXT STEPS:")
        print("   - Go to Django admin")
        print("   - Edit each product and check 'Is active'")
        print("   - Or run: UPDATE products_product SET is_active = TRUE;")
    else:
        print("✅ Everything looks good!")
        print(f"   You have {active_count} active products ready to display.")
    
    return True

if __name__ == "__main__":
    try:
        check_database()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

