# Nginx Reverse Proxy Setup Guide

This guide will help you set up nginx as a reverse proxy so your site is accessible at `http://fitness.lwsoc.com` (without the `:8000` port).

## What This Does

- Sets up nginx to listen on port 80 (HTTP)
- Proxies requests to your Django application running on port 8000
- Serves static files directly (faster)
- Allows access without specifying port number

## Prerequisites

- EC2 instance running
- Docker and Docker Compose installed
- Domain `fitness.lwsoc.com` pointing to your EC2 IP (`15.223.56.68`)

## Step 1: Update EC2 Security Group

1. Go to AWS Console → EC2 → Security Groups
2. Select your EC2 instance's security group
3. Add inbound rule:
   - **Type**: HTTP
   - **Port**: 80
   - **Source**: 0.0.0.0/0 (or restrict to specific IPs)
4. Click "Save rules"

## Step 2: Pull Latest Code on EC2

SSH into your EC2 instance and pull the latest code:

```bash
cd ~/online-fitness-store-M
git pull origin main
```

## Step 3: Update .env File

Make sure your `.env` file includes `fitness.lwsoc.com` in `ALLOWED_HOSTS`:

```bash
nano .env
```

Update:
```env
ALLOWED_HOSTS=fitness.lwsoc.com,ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
CSRF_TRUSTED_ORIGINS=http://fitness.lwsoc.com
```

## Step 4: Restart Docker Containers

Stop the current containers and restart with the new nginx configuration:

```bash
# Stop current containers
docker compose -f docker-compose.prod.yml down

# Start with new nginx service
docker compose -f docker-compose.prod.yml up -d --build
```

## Step 5: Verify Nginx is Running

Check that all containers are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

You should see:
- `fitness_db_prod` (database)
- `fitness_web_prod` (Django app)
- `fitness_nginx_prod` (nginx reverse proxy)

## Step 6: Test the Site

1. **Test via domain (port 80):**
   ```
   http://fitness.lwsoc.com
   ```

2. **Test via IP (port 80):**
   ```
   http://15.223.56.68
   ```

3. **Verify nginx logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs nginx
   ```

## Troubleshooting

### Port 80 Already in Use

If you get an error that port 80 is already in use:

```bash
# Check what's using port 80
sudo lsof -i :80

# Or
sudo netstat -tulpn | grep :80
```

If nginx (system) is running, stop it:
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Can't Access Site

1. **Check security group:** Make sure port 80 is open
2. **Check nginx logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs nginx
   ```
3. **Check web container logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs web
   ```
4. **Test nginx configuration:**
   ```bash
   docker compose -f docker-compose.prod.yml exec nginx nginx -t
   ```

### Static Files Not Loading

If static files aren't loading:

1. **Collect static files:**
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

2. **Restart nginx:**
   ```bash
   docker compose -f docker-compose.prod.yml restart nginx
   ```

### Still Need Direct Access to Port 8000

The web container still exposes port 8000 on localhost, so you can still access it directly from the EC2 instance:

```bash
curl http://localhost:8000
```

## Next Steps: HTTPS Setup (Optional but Recommended)

To set up HTTPS with Let's Encrypt:

1. Install certbot
2. Obtain SSL certificate
3. Update nginx configuration to use HTTPS
4. Add port 443 to security group

See `HTTPS_SETUP.md` for detailed instructions (to be created).

## Rollback

If you need to rollback to the old setup (without nginx):

1. Edit `docker-compose.prod.yml` and remove the nginx service
2. Change web service ports back to `"8000:8000"`
3. Restart:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

