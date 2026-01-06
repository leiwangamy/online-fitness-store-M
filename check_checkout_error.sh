#!/bin/bash
# Script to check checkout page error logs

echo "=== Checking Django logs ==="
docker compose -f docker-compose.prod.yml logs web --tail=50 | grep -i error

echo ""
echo "=== Checking recent web container logs ==="
docker compose -f docker-compose.prod.yml logs web --tail=100

echo ""
echo "=== Testing checkout view directly ==="
docker compose -f docker-compose.prod.yml exec web python manage.py shell << 'EOF'
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from payment.views import checkout

User = get_user_model()
factory = RequestFactory()

# Get a test user
try:
    user = User.objects.first()
    if user:
        request = factory.get('/payment/checkout/')
        request.user = user
        try:
            response = checkout(request)
            print(f"Response status: {response.status_code}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No users found in database")
except Exception as e:
    print(f"Error setting up test: {e}")
    import traceback
    traceback.print_exc()
EOF

