# Quick Start: Remove Port Number from URL

## Problem
Your site is accessible at `http://fitness.lwsoc.com:8000` but you want it at `http://fitness.lwsoc.com` (without port).

## Solution
Nginx reverse proxy has been configured. Follow these steps on your EC2 instance:

## Steps (Run on EC2)

### 1. Update Security Group
- AWS Console → EC2 → Security Groups
- Add inbound rule: **HTTP (port 80)** from **0.0.0.0/0**

### 2. Pull Latest Code
```bash
cd ~/online-fitness-store-P
git pull origin main
```

### 3. Update .env File
```bash
nano .env
```

Make sure it includes:
```env
ALLOWED_HOSTS=fitness.lwsoc.com,ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
CSRF_TRUSTED_ORIGINS=http://fitness.lwsoc.com
```

### 4. Restart Containers
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 5. Verify
```bash
# Check containers are running
docker compose -f docker-compose.prod.yml ps

# Check nginx logs
docker compose -f docker-compose.prod.yml logs nginx
```

### 6. Test
Visit: `http://fitness.lwsoc.com` (no port needed!)

## Troubleshooting

**Port 80 already in use?**
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

**Can't access site?**
- Check security group has port 80 open
- Check logs: `docker compose -f docker-compose.prod.yml logs nginx`

**Static files not loading?**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml restart nginx
```

## What Changed?

- ✅ Added nginx service to `docker-compose.prod.yml`
- ✅ Created `nginx/nginx.conf` configuration
- ✅ Nginx listens on port 80 and proxies to Django on port 8000
- ✅ Static files served directly by nginx (faster)

For detailed information, see `NGINX_SETUP.md`.

