"""
Quick script to test PostgreSQL connection
Run this to diagnose database connection issues:
    python test_db_connection.py
"""
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')

import django
django.setup()

from django.db import connection
from django.conf import settings

def test_connection():
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    
    db_config = settings.DATABASES['default']
    print(f"\nDatabase Configuration:")
    print(f"  Engine: {db_config['ENGINE']}")
    print(f"  Name: {db_config['NAME']}")
    print(f"  User: {db_config['USER']}")
    print(f"  Host: {db_config['HOST']}")
    print(f"  Port: {db_config['PORT']}")
    print(f"  Password: {'*' * len(db_config.get('PASSWORD', ''))}")
    
    print("\nAttempting to connect...")
    
    try:
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"\n✅ SUCCESS! Connected to PostgreSQL")
            print(f"   PostgreSQL version: {version}")
            
            # Check if database exists and is accessible
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"   Current database: {db_name}")
            
            # Check if we can query
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            print(f"   Query test: {result[0]}")
            
        print("\n✅ Database connection is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to database")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Verify database name exists: CREATE DATABASE fitness_club_db;")
        print("3. Verify user exists and has correct password")
        print("4. Check firewall/network settings if using remote host")
        print("5. Verify psycopg2-binary is installed: pip install psycopg2-binary")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

