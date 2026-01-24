# Quick Start: Company Settings

## Accessing the Settings

1. **Start the development server** (if not running):
   ```bash
   python manage.py runserver
   ```

2. **Log in to Django Admin**:
   - Go to: `http://127.0.0.1:8000/admin/`
   - Log in with your admin credentials

3. **Find Company Settings**:
   - In the left sidebar, look for **"Company Settings"**
   - Click on it
   - You'll be taken directly to the settings page

## What You Can Edit

### Company Branding
- **Company Name**: "Fitness Store" (change this to your actual company name)
- **Logo**: Upload your company logo (PNG recommended, max 200px wide)
- **Favicon**: Upload a small icon for browser tabs (16x16 or 32x32 px)
- **Tagline**: Add a catchy slogan

### Contact Information
- **Support Email**: Your customer support email
- **Phone Number**: Your business phone
- **Address**: Your physical business address

### Hero Section (Homepage)
- **Hero Title**: Main headline (currently: "Transform Your Fitness Journey")
- **Hero Subtitle**: Description text (max 500 characters)
- **Hero CTA Text**: Button text (currently: "Get Started")
- **Hero CTA URL**: Where the button goes (currently: "membership_plans")
- **Hero Image**: Optional background image for the hero section

## Where Settings Appear

### Header
- Company logo (if uploaded)
- Company name
- Tagline (if provided)

### Homepage
- Hero section title, subtitle, and CTA button
- Hero background image (if uploaded)

### Footer
- Company name in copyright notice
- Support email (if provided)

### Browser Tab
- Company name in page title
- Favicon icon (if uploaded) appears in the browser tab

## Quick Edit Examples

### Example 1: Update Company Name
1. Go to Admin → Company Settings
2. Change **Company Name** from "Fitness Store" to "Your Gym Name"
3. Click **Save**
4. Refresh your homepage - the name appears everywhere!

### Example 2: Add Your Logo
1. Go to Admin → Company Settings
2. Click **Choose File** next to **Logo**
3. Upload your logo image (PNG with transparent background works best)
4. Click **Save**
5. Your logo now appears in the header!

### Example 3: Add a Favicon
1. Go to Admin → Company Settings
2. Click **Choose File** next to **Favicon**
3. Upload a small icon (16x16 or 32x32 pixels, .ico or .png)
4. Click **Save**
5. Your icon now appears in browser tabs!

### Example 4: Change Hero Message
1. Go to Admin → Company Settings
2. Update **Hero Title** to: "New Year, New You!"
3. Update **Hero Subtitle** to: "Join our January special and get 30% off all memberships."
4. Click **Save**
5. Homepage hero section updates immediately!

## Common CTA URL Names

Use these Django URL names for the **Hero CTA URL** field:

| URL Name | Goes To |
|----------|---------|
| `members:membership_plans` | Membership plans page |
| `products:list` | All products page |
| `core:contact` | Contact page |
| `core:blog` | Blog listing |
| `home:home` | Homepage |
| `cart:cart_detail` | Shopping cart |

**Important:** Use the full namespaced URL (with the colon), not just the name!

## Tips

✅ **Save frequently** - Changes apply immediately
✅ **Test on homepage** - Visit `http://127.0.0.1:8000/` after changes
✅ **Keep it short** - Hero titles work best at 60-120 characters
✅ **Use action verbs** - CTA buttons: "Get Started", "Join Now", "Shop Now"
✅ **Optimize images** - Logos under 100KB, hero images under 500KB

## Need Help?

See the full documentation:
- **`COMPANY_SETTINGS_GUIDE.md`** - Comprehensive user guide
- **`COMPANY_SETTINGS_IMPLEMENTATION.md`** - Technical details

## Testing Your Changes

1. Make changes in the admin panel
2. Click **Save**
3. Visit `http://127.0.0.1:8000/` (homepage)
4. Check header for logo/name
5. Check hero section for your content
6. Scroll to footer for company name/email

That's it! You're all set to customize your site's branding. 🎉

