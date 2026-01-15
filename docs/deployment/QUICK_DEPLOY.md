# Quick Deployment Commands for AWS EC2

## On Your Local Machine (Before SSH)

1. **Push your code to GitHub** (if not already done):
```bash
git add .
git commit -m "Add production deployment configuration"
git push origin main
```

## On Your EC2 Instance (After SSH)

### Step 1: Update System and Install Docker
```bash
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Step 2: Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 3: Log out and back in (or run):
```bash
newgrp docker
```

### Step 4: Clone Your Repository
```bash
cd ~
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### Step 5: Create Production .env File
```bash
cp ec2.env.example .env
nano .env
```

**Update these values in .env:**
- `DJANGO_SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DJANGO_DEBUG=0` (should already be set)
- `ALLOWED_HOSTS=ec2-15-223-56-68.ca-central-1.compute.amazonaws.com`
- `POSTGRES_PASSWORD` - Set a strong password

### Step 6: Build and Start Containers
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 7: Run Migrations
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Step 8: Collect Static Files
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 9: Create Superuser (Optional)
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Verify Deployment

```bash
# Check containers are running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f web

# Test health endpoint
curl http://localhost:8000/health/
```

## Access Your Application

Visit: `http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000`

**Note:** Make sure your EC2 Security Group allows inbound traffic on port 8000!

## Quick Reference Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Start
docker compose -f docker-compose.prod.yml up -d
```

