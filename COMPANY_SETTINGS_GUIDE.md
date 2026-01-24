# Company Settings Guide

## Overview

The `CompanySettings` model provides a **centralized, unified system** to manage your website's branding, contact information, and hero section content through the Django admin panel. This is your single source of truth for all company-related information.

**Important:** This replaces the old `CompanyInfo` model, which is now deprecated.

## Features

### Company Branding
- **Company Name**: The name displayed in the header and page titles
- **Logo**: Company logo displayed in the header
- **Favicon**: Browser tab icon (optional)
- **Tagline**: A short slogan or tagline

### Contact Information
- **Support Email**: Contact email for customer support (appears in footer and contact page)
- **Phone Number**: Contact phone number (appears in contact page)
- **Address**: Physical business address (appears in contact page)

### Hero Section (Homepage)
- **Hero Title**: Main headline (max 120 characters)
- **Hero Subtitle**: Description text (max 500 characters)
- **Hero CTA Text**: Call-to-action button text (e.g., "Get Started")
- **Hero CTA URL**: Django URL name for the button (e.g., `membership_plans`)
- **Hero Image**: Background image for the hero section (optional)

## How to Use

### Accessing Settings

1. Log in to the Django admin panel at `/admin/`
2. Click on **"Company Settings"** in the sidebar
3. You'll be automatically redirected to the single settings instance
4. Make your changes and click **"Save"**

## Important Notes

### Single Instance
- **Single Instance**: Only ONE CompanySettings instance can exist
- **Cannot Delete**: The settings cannot be deleted (by design)
- **Auto-Created**: Default settings are created automatically on first migration

### Unified Settings (Replaces CompanyInfo)
**CompanySettings** is the unified system for all company information. The old `CompanyInfo` model is **deprecated** and should no longer be used:

- ✅ **Use**: Admin → Company Settings (for all company info)
- ❌ **Don't Use**: Admin → Company Information (deprecated, read-only)

All contact information (email, phone, address) has been migrated to CompanySettings. The contact page now pulls from CompanySettings automatically.

### Where Settings Appear

CompanySettings fields are used throughout your website:

| Field | Where It Appears |
|-------|------------------|
| Company Name | Header, footer, page titles |
| Logo | Header navigation bar |
| Favicon | Browser tab icon (next to page title) |
| Tagline | Header (next to company name) |
| Support Email | Footer, contact page |
| Phone Number | Contact page |
| Address | Contact page |
| Hero Title | Homepage hero section |
| Hero Subtitle | Homepage hero section |
| Hero CTA Button | Homepage hero section |
| Hero Image | Homepage hero background |

### Updating Hero Content

The hero section content can be changed without touching code:

**Example: Seasonal Campaign**
```
Hero Title: Spring into Fitness 2026!
Hero Subtitle: Join our Spring Challenge and save 20% on all memberships. Limited time offer!
Hero CTA Text: Join Now
Hero CTA URL: members:membership_plans
```

**Example: New Product Launch**
```
Hero Title: Introducing Our New Yoga Collection
Hero Subtitle: Premium yoga equipment and accessories designed for every level. Shop our exclusive collection today.
Hero CTA Text: Shop Yoga
Hero CTA URL: products:list
```

### Available URL Names for CTA

Common Django URL names you can use for the Hero CTA URL:

- `home:home` - Homepage
- `products:list` - All products page
- `members:membership_plans` - Membership plans
- `core:blog` - Blog listing
- `core:contact` - Contact page
- `cart:cart_detail` - Shopping cart

### Template Usage

The company settings are automatically available in all templates via the `company_settings` context processor.

**Examples:**
```html
<!-- Display company name -->
{{ company_settings.company_name }}

<!-- Display logo -->
{% if company_settings.logo %}
  <img src="{{ company_settings.logo.url }}" alt="{{ company_settings.company_name }}">
{% endif %}

<!-- Display hero title with fallback -->
{{ company_settings.hero_title|default:"Welcome to Our Site" }}

<!-- Display hero subtitle with line breaks -->
{{ company_settings.hero_subtitle|linebreaks }}

<!-- Support email link -->
{% if company_settings.support_email %}
  <a href="mailto:{{ company_settings.support_email }}">Contact Us</a>
{% endif %}
```

## Security Considerations

### HTML Safety
- All text fields are plain text only (no HTML)
- Use the `linebreaks` filter for multi-line content
- This prevents XSS (cross-site scripting) attacks

### Admin Access
- Only trusted staff/admin users should have access to Company Settings
- Changes are reflected site-wide immediately
- Test changes on a staging environment first for major updates

## Best Practices

### Images
- **Logo**: Use PNG with transparent background, max 200px wide, recommended height 50px
- **Favicon**: 16x16, 32x32, or 48x48 pixels, ICO or PNG format (appears in browser tabs)
- **Hero Image**: 1920x600 pixels recommended, under 500KB for fast loading

### Text Content
- **Hero Title**: Keep it punchy (60-120 characters)
- **Hero Subtitle**: Explain the value proposition (200-500 characters)
- **Tagline**: Short and memorable (20-40 characters)

### CTA Buttons
- Use action verbs: "Get Started", "Join Now", "Learn More", "Shop Now"
- Make sure the URL matches the button text
- Test the link after changing

## Troubleshooting

### Settings Not Showing Up?
- Check that `company_settings.context_processors.company_settings` is in `TEMPLATES` context processors
- Restart the development server after adding the app
- Run `python manage.py migrate` to create the database table

### Logo Not Displaying?
- Ensure `MEDIA_URL` and `MEDIA_ROOT` are configured in `settings.py`
- Check file upload permissions
- Verify the image file isn't corrupted

### CTA Button Link Not Working?
- Use Django URL names, not full URLs (e.g., `products:list` not `/products/`)
- Check the URL name is correct using `python manage.py show_urls` (if django-extensions installed)
- Or look in your `urls.py` files for the `name=` parameter

## Future Enhancements

Potential additions for future versions:
- Social media links (Facebook, Instagram, Twitter)
- Footer content management
- Multiple hero sections
- Rich text editor for hero subtitle
- A/B testing support
- Analytics integration

## Technical Details

### Model Location
`company_settings/models.py`

### Admin Configuration
`company_settings/admin.py`

### Context Processor
`company_settings/context_processors.py`

### Migrations
- `0001_initial.py` - Creates the table
- `0002_auto_*.py` - Populates default settings

## Support

If you need help or have questions:
1. Check this documentation first
2. Review the Django admin inline help text
3. Contact your development team
4. Refer to Django documentation at https://docs.djangoproject.com/

