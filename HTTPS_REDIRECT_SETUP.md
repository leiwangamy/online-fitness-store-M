# HTTPS Redirect Setup

This guide explains how to set up automatic HTTP to HTTPS redirect so all users are automatically redirected to the secure version of your site.

## What This Does

- **HTTP requests** (`http://fitness.lwsoc.com`) → Automatically redirected to HTTPS
- **HTTPS requests** (`https://fitness.lwsoc.com`) → Served securely
- All users always use the secure connection

## Prerequisites

- SSL certificate already set up (Let's Encrypt/certbot)
- Certificates located at `/etc/letsencrypt/live/fitness.lwsoc.com/`

## Step 1: Verify SSL Certificate Location

On your EC2 instance, check where your SSL certificates are:

```bash
ls -la /etc/letsencrypt/live/fitness.lwsoc.com/
```

You should see:
- `fullchain.pem`
- `privkey.pem`

**If your certificates are in a different location**, update the paths in `nginx/nginx.conf`:
```nginx
ssl_certificate /your/path/to/fullchain.pem;
ssl_certificate_key /your/path/to/privkey.pem;
```

## Step 2: Update Docker Compose

The `docker-compose.prod.yml` has been updated to mount the SSL certificates. If your certificates are in a different location, update the volume mount:

```yaml
volumes:
  - /your/cert/path:/etc/letsencrypt:ro
```

## Step 3: Pull Latest Code

```bash
cd ~/online-fitness-store-P
git pull origin main
```

## Step 4: Restart Containers

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

## Step 5: Test the Redirect

1. **Test HTTP redirect:**
   ```bash
   curl -I http://fitness.lwsoc.com
   ```
   Should return: `301 Moved Permanently` with `Location: https://fitness.lwsoc.com`

2. **Test HTTPS:**
   Visit `https://fitness.lwsoc.com` in your browser - should work securely

3. **Test automatic redirect:**
   Visit `http://fitness.lwsoc.com` in your browser - should automatically redirect to `https://fitness.lwsoc.com`

## Troubleshooting

### SSL Certificate Not Found

If nginx can't find the certificates:

1. **Check certificate location:**
   ```bash
   sudo ls -la /etc/letsencrypt/live/fitness.lwsoc.com/
   ```

2. **Update nginx.conf** with correct paths

3. **Update docker-compose.prod.yml** volume mount if needed

4. **Restart nginx:**
   ```bash
   docker compose -f docker-compose.prod.yml restart nginx
   ```

### Check Nginx Logs

```bash
docker compose -f docker-compose.prod.yml logs nginx
```

Look for SSL-related errors.

### Test Nginx Configuration

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

Should return: `nginx: configuration file /etc/nginx/nginx.conf test is successful`

## Security Benefits

✅ **All traffic encrypted** - No data sent in plain text  
✅ **Automatic redirect** - Users can't accidentally use HTTP  
✅ **HSTS header** - Browsers remember to use HTTPS  
✅ **SEO boost** - Google prefers HTTPS sites  
✅ **User trust** - Green padlock in browser  

## What Changed

- ✅ HTTP server block now redirects to HTTPS
- ✅ HTTPS server block configured with SSL
- ✅ Security headers added (HSTS, etc.)
- ✅ Docker Compose mounts SSL certificates

Your site is now fully secure! 🔒

