# Deployment Steps for Online Changes

## Quick Deployment (After Code is Pushed to GitHub)

Your code is already pushed to GitHub! Now deploy to production:

### Step 1: SSH to Your EC2 Instance

```bash
ssh -i your-key.pem ec2-user@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
```

(Replace `your-key.pem` with your actual SSH key file path)

### Step 2: Navigate to Your Project Directory

```bash
cd ~/online-fitness-store-M
# Or wherever you cloned the repository
```

### Step 3: Pull Latest Changes from GitHub

```bash
git pull origin main
```

This will download all your latest changes including:
- New manage subscription page
- Updated membership features
- Blog features
- All migrations

### Step 4: Run Database Migrations

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

This will apply any new database migrations (like the new MembershipPlan model, BlogPostImage, etc.)

### Step 5: Collect Static Files

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

This updates static files (CSS, JS) if any were changed.

### Step 6: Restart Containers

```bash
docker compose -f docker-compose.prod.yml restart web
```

Or rebuild if needed:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 7: Verify Deployment

Check that everything is running:

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f web

# Check containers are running
docker compose -f docker-compose.prod.yml ps
```

Visit your site:
```
http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000
```

## Quick One-Line Deployment

If you're already in the project directory on EC2:

```bash
git pull && docker compose -f docker-compose.prod.yml exec web python manage.py migrate && docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput && docker compose -f docker-compose.prod.yml restart web
```

## What Gets Deployed

✅ All your code changes (templates, views, models, etc.)
✅ New migrations (MembershipPlan, BlogPostImage, etc.)
✅ Updated static files
✅ New manage subscription page
✅ Membership features updates

## What Does NOT Get Deployed

❌ Your local `.env` file (stays on your machine)
❌ Your local database backup (stays on your machine)
❌ `ACCOUNT_EMAIL_VERIFICATION=none` (production uses its own environment variables)

## Troubleshooting

If you encounter issues:

1. **Check logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f web
   ```

2. **Check if containers are running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

3. **Rebuild containers if needed:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Check database connection:**
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py dbshell
   ```

