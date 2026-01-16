# Migration Instructions for Blog and Membership Content Models

## Issue
The 502 Bad Gateway error is likely occurring because the new models (`BlogPost` and `MembershipPlanContent`) have been added to the code but the database migrations haven't been run yet on the production server.

## Steps to Fix

### 1. On the Production Server (via SSH/Docker)

```bash
# Navigate to project directory
cd ~/online-fitness-store-M

# Pull latest changes (if not already done)
git pull origin main

# Run migrations inside Docker container
docker compose -f docker-compose.prod.yml exec web python manage.py makemigrations core
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Restart the web container to apply changes
docker compose -f docker-compose.prod.yml restart web
```

### 2. Verify the Migration

Check that the migrations were created and applied:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations core
```

You should see:
```
core
 [X] 0001_initial
 [X] 0002_blogpost_membershipplancontent  (or similar)
```

### 3. Access Admin Panel

After migrations are complete:
1. Go to `https://fitness.lwsoc.com/admin/`
2. You should now see:
   - **Blog Posts** - to create and manage blog posts
   - **Membership Plan Content** - to edit membership page content

## New Admin Features

### Blog Posts
- **Location**: Admin → Blog Posts
- **Features**:
  - Create blog posts with title, content, excerpt
  - Upload featured images
  - Set publish status and date
  - View post statistics (view count)
  - SEO-friendly slugs auto-generated from title

### Membership Plan Content
- **Location**: Admin → Membership Plan Content
- **Features**:
  - Edit page title and intro text
  - Customize Basic plan name, description, and details
  - Customize Premium plan name, description, and details
  - Singleton pattern (only one instance exists)

## Notes

- The code is defensive and will work even if migrations aren't run yet (it will use default/empty content)
- However, running migrations is required for full functionality
- After migrations, create a MembershipPlanContent instance in admin to customize the membership page
- Blog posts need to be marked as "Published" to appear on the public blog page

