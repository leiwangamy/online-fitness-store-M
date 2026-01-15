# Deploy Changes to Production

## Steps to Deploy on EC2 Server

### 1. SSH into your EC2 server:
```bash
ssh -i ~/Downloads/fitness-key.pem ubuntu@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
```

### 2. Navigate to your project directory:
```bash
cd ~/online-fitness-store-P
```

### 3. Pull the latest changes from GitHub:
```bash
git pull origin main
```

### 4. Run migrations (to add the is_featured field):
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 5. Collect static files (if needed):
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 6. Restart the web container:
```bash
docker compose -f docker-compose.prod.yml restart web
```

### 7. Verify the deployment:
```bash
docker compose -f docker-compose.prod.yml logs web --tail 50
```

## Quick One-Line Command (if you're already in the project directory):
```bash
git pull origin main && docker compose -f docker-compose.prod.yml exec web python manage.py migrate && docker compose -f docker-compose.prod.yml restart web
```

After deployment, the "Is featured" field should appear in the admin panel on the production site!

