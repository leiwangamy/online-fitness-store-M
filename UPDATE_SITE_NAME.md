# Update Site Name from "example.com" to Your Site Name

The "example.com" text in your verification emails comes from Django's Sites framework. Here's how to change it.

## Option 1: Update via Django Admin (Easiest)

1. Log into your Django admin: `http://15.223.56.68:8000/admin/`
2. Go to **Sites** → **Sites**
3. Click on the site (usually ID=1, named "example.com")
4. Update:
   - **Domain name**: `ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000` (MUST include :8000 port!)
   - **Display name**: `Fitness Club` (or your preferred name)
5. Click **Save**

## Option 2: Update via Django Shell (On EC2)

SSH into your EC2 instance and run:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

Then in the Python shell:

```python
from django.contrib.sites.models import Site

# Get the site (usually ID=1)
site = Site.objects.get(id=1)

# Update the domain and name (MUST include :8000 port for email links to work!)
site.domain = 'ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000'
site.name = 'Fitness Club'
site.save()

# Verify the change
print(f"Site updated: {site.name} - {site.domain}")
```

## Option 3: Update via Management Command (One-time)

Create a management command to update the site automatically.

## What This Changes

After updating, your verification emails will show:
- **Before**: "Hello from example.com!"
- **After**: "Hello from Fitness Club!" (or whatever name you set)

The confirmation link will still work the same way, but the branding will be correct.

