# Complete Local Testing Guide

A comprehensive guide for testing your Django Fitness Club application locally using Docker.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start - Every Time You Test](#quick-start---every-time-you-test)
3. [Initial Setup (First Time Only)](#initial-setup-first-time-only)
4. [Daily Testing Workflow](#daily-testing-workflow)
5. [Feature Testing Guide](#feature-testing-guide)
6. [Useful Commands](#useful-commands)
7. [Troubleshooting](#troubleshooting)
8. [Testing Checklist](#testing-checklist)

---

## Prerequisites

Before you begin, make sure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **PowerShell** or **Windows Terminal** (for Windows)
- ✅ **Git repository** cloned locally
- ✅ Project directory: `C:\Users\Lei\Documents\VS Code Projects\online-fitness-store P`

---

## Quick Start - Every Time You Test

**Yes, Docker Desktop needs to be running**, but you don't need to use its UI - just make sure it's started.

### Step 1: Start Docker Desktop (if not already running)

1. Open **Docker Desktop** application
2. Wait for it to fully start (whale icon in system tray should be steady - can take 1-2 minutes)
3. You don't need to do anything else in the UI!

**Verify Docker is running:**
```powershell
docker --version
docker ps
```
Both commands should work without errors.

### Step 2: Start the Containers

Run this command in PowerShell:

```powershell
cd "C:\Users\Lei\Documents\VS Code Projects\online-fitness-store P"
docker compose up -d
```

This will:
- ✅ Start the database container (`fitness_db`)
- ✅ Start the web server container (`fitness_web`)
- ✅ Make the site available at http://localhost:8000

**Check if containers are running:**
```powershell
docker compose ps
```

You should see both `fitness_web` and `fitness_db` with status "Up".

### Step 3: Access the Application

Open your web browser and go to:

- **Homepage**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **Blog Page**: http://localhost:8000/blog/
- **Membership Page**: http://localhost:8000/membership/

### Step 4: Stop the Containers (when done testing)

```powershell
docker compose down
```

**Note:** Closing Docker Desktop UI does **NOT** stop containers. Always use `docker compose down` to stop them properly.

---

## Initial Setup (First Time Only)

### Step 1: Run Migrations

The migrations need to be run to create the database tables:

```powershell
# Navigate to project directory
cd "C:\Users\Lei\Documents\VS Code Projects\online-fitness-store P"

# Create migrations for new models (if any)
docker compose exec web python manage.py makemigrations

# Apply all migrations
docker compose exec web python manage.py migrate
```

You should see output like:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, ...
Running migrations:
  Applying core.0002_blogpost_membershipplancontent... OK
    - Create model BlogPost
    - Create model MembershipPlanContent
```

### Step 2: Create Superuser (if needed)

If you don't have an admin account yet:

```powershell
docker compose run --rm web python manage.py createsuperuser
```

**Note:** The local database is separate from production, so you can:
- Use the **same username/password as production** (recommended for consistency)
- Use different credentials if you prefer

**OR** if you already have a superuser, skip this step.

---

## Daily Testing Workflow

### Starting Your Testing Session

1. **Start Docker Desktop** (if not running)
2. **Start containers**: `docker compose up -d`
3. **Verify**: Visit http://localhost:8000
4. **Begin testing** features

### Ending Your Testing Session

1. **Stop containers**: `docker compose down`
2. **Optionally close Docker Desktop** (if you want to free up resources)

---

## Feature Testing Guide

### Test Blog Content Management

#### Create a Blog Post:

1. **Go to Admin Panel**: http://localhost:8000/admin/
2. **Login** with your superuser credentials
3. **Click "Blog Posts"** under the CORE section
4. **Click "Add Blog Post"**
5. **Fill in the form**:
   - **Title**: "Welcome to Our Fitness Blog"
   - **Slug**: Will auto-generate from title (or customize it)
   - **Author**: "Fitness Club" (or your name)
   - **Content**: Enter your blog post content (HTML is supported)
   - **Excerpt**: Short summary (optional, max 500 characters)
   - **Featured Image**: Upload an image (optional)
   - **Is Published**: ✅ **Check this box** to make it visible (important!)
   - **Published Date**: Will auto-set when you check "Is Published"
6. **Click "Save"**
7. **Visit**: http://localhost:8000/blog/ to see your post

#### Test Blog Features:

- ✅ Create multiple blog posts
- ✅ Edit existing posts
- ✅ Unpublish a post (uncheck "Is Published") - it should disappear from the public blog
- ✅ View individual blog post detail pages (click on a post title)
- ✅ Test pagination (create 11+ posts to see pagination)
- ✅ Verify only published posts appear on the public blog page

### Test Membership Content Management

#### Edit Membership Page Content:

1. **In Admin Panel**, click **"Membership Plan Content"** under CORE
2. You'll see a single form (singleton pattern) with:
   - **Page Title**: "Membership Plans"
   - **Intro Text**: Introduction message for the membership page
   - **Basic Plan** section:
     - Name, Description, Details
   - **Premium Plan** section:
     - Name, Description, Details
3. **Edit the content** as desired
4. **Click "Save"**
5. **Visit**: http://localhost:8000/membership/ to see your changes

#### Test Membership Features:

- ✅ Edit page title and intro text
- ✅ Customize Basic plan information (Name: "Basic", Price: "Free")
- ✅ Customize Premium plan information (Name: "Premium", Price: "$20")
- ✅ Verify changes appear on the membership page
- ✅ Check that default values show if content is empty

### Test Account Dropdown Menu

1. **Login** to the site (not just admin panel)
2. **Look at the navigation bar** - you should see an "Account" dropdown menu
3. **Click the Account dropdown** to see:
   - Profile
   - Billing / Payments
   - Manage Subscription
   - Logout
4. **Test each link**:
   - Profile should show user profile page
   - Billing / Payments should show billing page
   - Manage Subscription should redirect to membership page
   - Logout should log you out

### Test Other Pages

Visit these URLs to verify they work:

- **Blog List**: http://localhost:8000/blog/
- **Blog Detail** (replace `slug` with actual slug): http://localhost:8000/blog/your-post-slug/
- **Membership Plans**: http://localhost:8000/membership/
- **My Membership** (requires login): http://localhost:8000/membership/my/
- **Billing/Payments** (requires login): http://localhost:8000/billing/
- **Manage Subscription** (requires login): http://localhost:8000/membership/manage/

---

## Useful Commands

All these commands work in **PowerShell**:

### Container Management

```powershell
# Start containers in background
docker compose up -d

# Stop containers
docker compose down

# Restart containers
docker compose restart

# Stop and remove all containers (including volumes)
docker compose down -v

# View running containers
docker compose ps

# Rebuild after code changes
docker compose up --build -d
```

### Django Management Commands

```powershell
# Create migrations
docker compose exec web python manage.py makemigrations

# Apply migrations
docker compose exec web python manage.py migrate

# Check migration status
docker compose exec web python manage.py showmigrations core

# Create superuser
docker compose run --rm web python manage.py createsuperuser

# Access Django shell
docker compose exec web python manage.py shell

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

### Logs and Debugging

```powershell
# View web server logs
docker compose logs web

# View database logs
docker compose logs db

# Follow logs in real-time (press Ctrl+C to exit)
docker compose logs -f web

# View last 50 lines of logs
docker compose logs web --tail 50

# View all logs
docker compose logs
```

### Database Commands

```powershell
# Access PostgreSQL shell
docker compose exec db psql -U postgres -d fitness_club

# Backup database
docker compose exec db pg_dump -U postgres fitness_club > backup.sql

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Troubleshooting

### Docker Desktop Not Running

**Error:**
```
Cannot connect to the Docker daemon
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

**Solution:**
1. **Start Docker Desktop:**
   - Press `Windows key` and search for "Docker Desktop"
   - Click to launch Docker Desktop
   - Wait for it to fully start (you'll see a whale icon in the system tray)
   - The icon should be steady (not animating) when ready (this can take 1-2 minutes)

2. **Verify Docker is running:**
   ```powershell
   docker --version
   docker ps
   ```
   Both commands should work without errors.

3. **If Docker Desktop won't start:**
   - Make sure Windows Subsystem for Linux (WSL 2) is installed and updated
   - Restart your computer
   - Check Windows Updates
   - Reinstall Docker Desktop if needed

### Can't Access http://localhost:8000

**Check if containers are running:**
```powershell
docker compose ps
```

**Should show:**
- `fitness_web` with status "Up" and ports "0.0.0.0:8000->8000/tcp"
- `fitness_db` with status "Up"

**If containers are not running:**
```powershell
# Start them
docker compose up -d

# Check logs for errors
docker compose logs web
```

**If containers are running but site won't load:**
```powershell
# Check logs for errors
docker compose logs web --tail 50

# Restart the web container
docker compose restart web
```

### Port 8000 Already in Use

**Check what's using the port:**
```powershell
netstat -ano | findstr :8000
```

**Solution:**
```powershell
# Stop existing containers
docker compose down

# Or kill the process using port 8000 (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### "docker compose" Command Not Found

**Solution:**
- Make sure Docker Desktop is installed and running
- Try `docker-compose` (with hyphen) instead of `docker compose`
- Update Docker Desktop to latest version
- Restart PowerShell/terminal

### Database Errors

**Error: "relation does not exist" or "no such table"**

**Solution:**
```powershell
# Run migrations
docker compose exec web python manage.py migrate

# If that doesn't work, check migration status
docker compose exec web python manage.py showmigrations
```

**Error: "database connection failed"**

**Solution:**
```powershell
# Check if database container is running
docker compose ps

# Restart containers
docker compose restart

# Check database logs
docker compose logs db
```

### Don't See New Models in Admin

**Check:**
- Make sure you're logged in as superuser
- Models should appear under "CORE" section
- Run migrations: `docker compose exec web python manage.py migrate`
- Restart container: `docker compose restart web`
- Check container logs: `docker compose logs web`

### Blog Posts Don't Appear on Public Page

**Solution:**
- Check that **"Is Published"** is checked
- Check that **"Published Date"** is set (auto-sets when you check "Is Published")
- Verify you're viewing published posts only (the view filters for `is_published=True`)
- Clear browser cache and reload
- Check logs for errors: `docker compose logs web`

### Membership Page Shows Defaults Instead of Admin Content

**Solution:**
- Make sure you've created a **MembershipPlanContent** instance in admin
- Check that migrations were run successfully: `docker compose exec web python manage.py showmigrations core`
- Verify the view is loading content correctly (check logs)
- Make sure you saved the content in admin panel

### Container Keeps Restarting

**Solution:**
```powershell
# Check logs for errors
docker compose logs web --tail 50

# Restart the container
docker compose restart web

# If that doesn't work, rebuild
docker compose up --build -d
```

### "No module named 'django'" or Other Python Errors

**Solution:**
- Make sure you're using Docker commands (not running Python directly)
- Rebuild the container: `docker compose up --build -d`
- Check requirements.txt is correct
- Check Dockerfile is correct

---

## Testing Checklist

Use this checklist to verify everything is working:

### Initial Setup
- [ ] Docker Desktop installed and running
- [ ] Containers start successfully (`docker compose up -d`)
- [ ] Migrations run successfully
- [ ] Superuser created
- [ ] Can access http://localhost:8000

### Admin Panel
- [ ] Can log in to admin panel
- [ ] See "Blog Posts" under CORE section
- [ ] See "Membership Plan Content" under CORE section
- [ ] Can create, edit, and delete blog posts
- [ ] Can edit membership plan content

### Blog Features
- [ ] Can create a blog post
- [ ] Blog post appears on public blog page (`/blog/`)
- [ ] Can edit blog post
- [ ] Unpublished posts don't appear publicly
- [ ] Blog detail pages load correctly
- [ ] Images upload correctly for blog posts
- [ ] Pagination works on blog list page (if 11+ posts)

### Membership Features
- [ ] Can edit membership plan content in admin
- [ ] Membership page (`/membership/`) displays edited content
- [ ] Basic membership shows "Free" price
- [ ] Premium membership shows "$20" price
- [ ] Default values work when content is empty

### Navigation and UI
- [ ] Account dropdown appears when logged in
- [ ] Account dropdown has: Profile, Billing/Payments, Manage Subscription, Logout
- [ ] Blog link appears in navigation
- [ ] No "Sign Up" link in navigation (only "Sign In")
- [ ] All navigation links work correctly

### Pages and URLs
- [ ] Homepage loads correctly
- [ ] Blog page (`/blog/`) loads correctly
- [ ] Membership page (`/membership/`) loads correctly
- [ ] Profile page loads (when logged in)
- [ ] Billing/Payments page loads (when logged in)
- [ ] Manage Subscription redirects correctly

### Functionality
- [ ] User can sign in
- [ ] User can sign out
- [ ] User can register (via sign-in page)
- [ ] Protected pages require authentication
- [ ] All forms work correctly

---

## Additional Notes

- **Docker Desktop must be running** for all Docker commands to work
- **Closing Docker Desktop UI does NOT stop containers** - always use `docker compose down`
- The local database is **separate from production** - changes don't affect production
- Blog posts need to be marked as **"Published"** to appear publicly
- Membership content uses a **singleton pattern** (only one instance exists)
- Images are stored in `media/blog_images/` directory
- All HTML content in blog posts is rendered safely (Django's template filters handle this)
- The code is defensive and will work even if migrations aren't run (uses defaults)

---

## Next Steps

Once you've tested locally and everything works:

1. **Commit your changes:**
   ```powershell
   git add .
   git commit -m "Add blog and membership content management features"
   ```

2. **Push to GitHub:**
   ```powershell
   git push origin main
   ```

3. **Deploy to production** (see `MIGRATION_INSTRUCTIONS.md` for production deployment steps)

---

## PowerShell Tips

- **Copy/Paste**: Right-click in PowerShell to paste, or use `Ctrl+V` (depending on PowerShell version)
- **Multi-line commands**: Use backtick `` ` `` at end of line for continuation
- **Clear screen**: `cls` or `Clear-Host`
- **Exit**: `exit` or close the window
- **Navigate to project**: Always use quotes for path with spaces:
  ```powershell
  cd "C:\Users\Lei\Documents\VS Code Projects\online-fitness-store P"
  ```

---

**Last Updated**: [Current Date]
**Version**: 1.0
