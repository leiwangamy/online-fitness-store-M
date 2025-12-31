# Quick Fix Commands for EC2

## Problem: Missing .env file

Run these commands on your EC2 instance:

```bash
# 1. Navigate to your project directory
cd ~/online-fitness-store-P

# 2. Create .env file from the example
cp ec2.env.example .env

# 3. Edit .env file with your production values
nano .env
```

## Required Updates in .env file:

1. **Generate a Django secret key:**
   ```bash
   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output and paste it as `DJANGO_SECRET_KEY` value

2. **Set DJANGO_DEBUG=0** (should already be set)

3. **Set ALLOWED_HOSTS:**
   ```
   ALLOWED_HOSTS=ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
   ```

4. **Set a strong POSTGRES_PASSWORD:**
   Change `your-secure-database-password-change-this` to a strong password

## After creating .env file:

```bash
# Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

# Check if containers are running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

## If you still get errors:

Make sure the .env file exists:
```bash
ls -la .env
cat .env  # Verify it has content
```

