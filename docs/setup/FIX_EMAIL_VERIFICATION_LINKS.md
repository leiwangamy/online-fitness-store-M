# Fix Email Verification Links

## Problem
Email verification links don't work - connection refused error. The links are missing the port `:8000` or using the wrong domain.

## Solution

Django-allauth uses the Django Sites framework to generate email links. We need to update the Site domain to include the port.

### On EC2, run these commands:

1. **SSH into EC2:**
   ```bash
   ssh -i ~/Downloads/fitness-key.pem ubuntu@15.223.56.68
   ```

2. **Open Django shell:**
   ```bash
   cd ~/online-fitness-store-M
   docker compose -f docker-compose.prod.yml exec web python manage.py shell
   ```

3. **Update the Site domain (in the Python shell):**
   ```python
   from django.contrib.sites.models import Site
   
   # Get the site (usually ID=1)
   site = Site.objects.get(id=1)
   
   # Update domain to include port 8000
   site.domain = 'ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000'
   site.name = 'Fitness Club'
   site.save()
   
   # Verify it's updated
   print(f"Domain: {site.domain}")
   print(f"Name: {site.name}")
   
   # Exit shell
   exit()
   ```

4. **Alternative: Update via Admin Panel**
   - Go to: `http://ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000/admin/`
   - Navigate to: Sites → Sites → example.com (or the site with ID=1)
   - Change:
     - **Domain name**: `ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000`
     - **Display name**: `Fitness Club`
   - Click Save

## Check if Containers are Running

If you're getting connection refused, also check if containers are running:

```bash
docker compose -f docker-compose.prod.yml ps
```

If containers are not running, start them:

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Check Security Group

Make sure port 8000 is open in AWS Security Group:
- Go to EC2 Console → Security Groups
- Select your security group
- Inbound rules should allow TCP port 8000 from 0.0.0.0/0 (or your IP)

## Test

After updating the Site domain:
1. Try signing up with a new email
2. Check the email - the verification link should now include `:8000`
3. The link should work when clicked

## Important Notes

- **With Port**: Domain should be `ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:8000`
- **Without Port**: Only if you set up a reverse proxy (nginx) on port 80/443
- The domain in the Site model must match what's in your `.env` ALLOWED_HOSTS (without port)

