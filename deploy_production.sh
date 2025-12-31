#!/bin/bash
# Production Deployment Script
# Run this after setting up .env file on EC2

set -e  # Exit on error

echo "========================================="
echo "Production Deployment"
echo "========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create .env file from ec2.env.example and update all values."
    exit 1
fi

# Check if DJANGO_DEBUG is set to 0
if grep -q "DJANGO_DEBUG=1" .env; then
    echo "⚠️  WARNING: DJANGO_DEBUG is set to 1 in .env"
    echo "   This should be 0 for production!"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 1: Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "Step 2: Waiting for database to be ready..."
sleep 10

echo ""
echo "Step 3: Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo ""
echo "Step 4: Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Your application should now be running at:"
echo "  http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000"
echo ""
echo "Useful commands:"
echo "  View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  Stop: docker compose -f docker-compose.prod.yml down"
echo "  Restart: docker compose -f docker-compose.prod.yml restart"
echo ""

