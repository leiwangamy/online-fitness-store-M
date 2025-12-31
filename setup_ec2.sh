#!/bin/bash
# AWS EC2 Production Setup Script
# Run this script on your EC2 instance to set up Docker and deploy the application

set -e  # Exit on error

echo "========================================="
echo "AWS EC2 Production Setup"
echo "========================================="

# Step 1: Update system packages
echo ""
echo "Step 1: Updating system packages..."
sudo yum update -y

# Step 2: Install Docker
echo ""
echo "Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
else
    echo "Docker is already installed."
fi

# Step 3: Install Docker Compose
echo ""
echo "Step 3: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully!"
else
    echo "Docker Compose is already installed."
fi

# Step 4: Verify installations
echo ""
echo "Step 4: Verifying installations..."
docker --version
docker-compose --version

# Step 5: Create .env file from example if it doesn't exist
echo ""
echo "Step 5: Setting up environment file..."
if [ ! -f .env ]; then
    if [ -f ec2.env.example ]; then
        cp ec2.env.example .env
        echo "Created .env file from ec2.env.example"
        echo "⚠️  IMPORTANT: Edit .env file and update all values before continuing!"
        echo "   - Set DJANGO_SECRET_KEY to a secure random string"
        echo "   - Set POSTGRES_PASSWORD to a secure password"
        echo "   - Verify ALLOWED_HOSTS matches your EC2 DNS"
    else
        echo "⚠️  WARNING: ec2.env.example not found. Please create .env manually."
    fi
else
    echo ".env file already exists."
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your production values"
echo "2. Run: docker compose up -d --build"
echo "3. Run: docker compose exec web python manage.py migrate"
echo "4. Run: docker compose exec web python manage.py collectstatic --noinput"
echo ""
echo "Note: You may need to log out and back in for Docker group changes to take effect."
echo "      Or run: newgrp docker"

