# AWS EC2 Deployment Guide

This guide will help you deploy your Django fitness store application to AWS EC2.

## Prerequisites

- AWS EC2 instance running Amazon Linux 2 or Ubuntu
- SSH access to your EC2 instance
- Your EC2 DNS: `ec2-15-223-56-68.ca-central-1.compute.amazonaws.com`

## Step 1: Connect to Your EC2 Instance

```bash
ssh -i your-key.pem ec2-user@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
```

(Replace `your-key.pem` with your actual key file)

## Step 2: Install Git (if not already installed)

```bash
# Amazon Linux 2
sudo yum install -y git

# Ubuntu
sudo apt-get update && sudo apt-get install -y git
```

## Step 3: Clone Your Repository

```bash
cd ~
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

## Step 4: Run the Setup Script

```bash
chmod +x setup_ec2.sh
./setup_ec2.sh
```

This script will:
- Update system packages
- Install Docker and Docker Compose
- Create a `.env` file from `ec2.env.example`

**Important:** After the script completes, you may need to log out and back in (or run `newgrp docker`) for Docker group changes to take effect.

## Step 5: Configure Environment Variables

Edit the `.env` file with your production values:

```bash
nano .env
```

**Required changes:**
1. Set `DJANGO_SECRET_KEY` to a secure random string (you can generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
2. Set `DJANGO_DEBUG=0` (should already be set)
3. Set `ALLOWED_HOSTS=ec2-15-223-56-68.ca-central-1.compute.amazonaws.com`
4. Set `POSTGRES_PASSWORD` to a strong password
5. If you have a custom domain with SSL, add it to `CSRF_TRUSTED_ORIGINS`

Example `.env` file:
```env
DJANGO_SECRET_KEY=your-generated-secret-key-here
DJANGO_DEBUG=0
ALLOWED_HOSTS=ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
POSTGRES_DB=fitness_club_db
POSTGRES_USER=fitness_user
POSTGRES_PASSWORD=your-secure-password-here
DB_HOST=db
POSTGRES_PORT=5432
```

## Step 6: Deploy the Application

Run the deployment script:

```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

This will:
- Build and start Docker containers
- Run database migrations
- Collect static files
- Start the application with Gunicorn

## Step 7: Configure Security Group

Make sure your EC2 Security Group allows inbound traffic on:
- **Port 8000** (HTTP) - for your Django application
- **Port 22** (SSH) - for SSH access
- **Port 80/443** (if using nginx as reverse proxy)

## Step 8: Test Your Application

Visit your application:
```
http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000
```

Test the health check endpoint:
```
http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000/health/
```

## Manual Commands (Alternative to Scripts)

If you prefer to run commands manually:

```bash
# 1. Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

# 2. Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 3. Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# View web logs only
docker compose -f docker-compose.prod.yml logs -f web

# Stop containers
docker compose -f docker-compose.prod.yml down

# Restart containers
docker compose -f docker-compose.prod.yml restart

# Access Django shell
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Setting Up Nginx (Optional but Recommended)

For production, you should set up nginx as a reverse proxy:

1. Install nginx:
```bash
sudo yum install -y nginx  # Amazon Linux 2
# or
sudo apt-get install -y nginx  # Ubuntu
```

2. Create nginx configuration:
```bash
sudo nano /etc/nginx/conf.d/fitness_club.conf
```

Add:
```nginx
server {
    listen 80;
    server_name ec2-15-223-56-68.ca-central-1.compute.amazonaws.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }
}
```

3. Start nginx:
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Troubleshooting

### Docker permission denied
```bash
# Add your user to docker group (if not done by script)
sudo usermod -aG docker $USER
newgrp docker
```

### Port already in use
```bash
# Check what's using port 8000
sudo lsof -i :8000
# Or change the port in docker-compose.prod.yml
```

### Database connection errors
- Check that `DB_HOST=db` in your `.env` file
- Verify database container is running: `docker compose -f docker-compose.prod.yml ps`

### Static files not loading
- Run `collectstatic` again: `docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput`
- Check `STATIC_ROOT` in settings.py
- Verify WhiteNoise middleware is enabled

## Next Steps

- Set up SSL certificate with Let's Encrypt
- Configure domain name DNS
- Set up automated backups
- Configure monitoring and logging
- Set up email service for production

