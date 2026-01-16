# Project Structure Documentation

This document provides a detailed overview of the project structure, explaining the purpose of each directory and key files.

## 📁 Directory Structure

```
online-fitness-store-M/
│
├── accounts/                    # User authentication and account management
│   ├── __init__.py
│   ├── adapters.py             # Django-allauth custom adapters
│   ├── admin.py                # Admin panel configuration
│   ├── backends.py             # Custom authentication backends
│   ├── forms.py                # User registration and account forms
│   ├── models.py               # User-related models (if any)
│   ├── urls.py                 # URL routing for accounts app
│   └── views.py                # Account-related views
│
├── api/                         # REST API endpoints (optional/experimental)
│   ├── admin.py
│   ├── models.py
│   └── views.py
│
├── cart/                        # Shopping cart functionality
│   ├── models.py                # CartItem model
│   ├── urls.py                  # Cart URL routes
│   └── views.py                 # Add to cart, remove, update quantities
│
├── core/                        # Core utilities and shared functionality
│   ├── admin.py                 # Admin panel customizations
│   ├── admin_actions.py         # Custom admin actions
│   ├── admin_mixins.py         # Reusable admin mixins
│   ├── models.py                # Shared models (e.g., Contact)
│   ├── urls.py                  # Core URL routes (e.g., contact page)
│   └── views.py                 # Shared views
│
├── fitness_club/                # Main Django project package
│   └── fitness_club/            # Project settings and configuration
│       ├── __init__.py
│       ├── settings.py          # Django settings (database, apps, etc.)
│       ├── urls.py              # Root URL configuration
│       ├── wsgi.py              # WSGI configuration for deployment
│       └── asgi.py              # ASGI configuration (for async)
│
├── home/                        # Home page and landing
│   ├── models.py                # Home page models (if any)
│   ├── urls.py                  # Home page URL routes
│   └── views.py                 # Home page view (product listing)
│
├── members/                      # Membership management
│   ├── models.py                 # Membership models
│   ├── forms.py                  # Membership forms
│   ├── signals.py                # Django signals for memberships
│   ├── urls.py                   # Membership URL routes
│   └── views.py                  # Membership views
│
├── orders/                       # Order processing and management
│   ├── models.py                 # Order, OrderItem, PickupLocation models
│   ├── forms.py                  # Order and shipping address forms
│   ├── services.py               # Order processing services (digital downloads)
│   ├── admin.py                  # Order admin panel configuration
│   ├── urls.py                   # Order URL routes
│   ├── views_orders.py           # Order viewing and management views
│   └── views_downloads.py         # Digital download views
│
├── payment/                      # Checkout and payment processing
│   ├── models.py                 # Payment-related models (if any)
│   ├── forms.py                  # Payment forms
│   ├── urls.py                   # Payment/checkout URL routes
│   └── views.py                  # Checkout view, payment processing
│
├── products/                     # Product catalog and management
│   ├── models.py                 # Product, Category, ProductImage models
│   ├── forms.py                  # Product admin forms
│   ├── inventory.py              # Inventory management utilities
│   ├── admin.py                  # Product admin panel configuration
│   ├── urls.py                    # Product URL routes
│   └── views.py                  # Product listing and detail views
│
├── profiles/                     # User profile management
│   ├── models.py                 # UserProfile model (shipping addresses)
│   ├── forms.py                  # Profile editing forms
│   ├── signals.py                # Signals to create profiles automatically
│   ├── urls.py                   # Profile URL routes
│   └── views.py                  # Profile views
│
├── static/                       # Static files (CSS, JavaScript, images)
│   ├── css/
│   │   ├── admin_custom.css      # Custom Django admin styling
│   │   └── style.css             # Main application styles
│   └── js/
│       └── product_admin.js      # JavaScript for product admin
│
├── templates/                    # HTML templates
│   ├── base.html                 # Base template (navigation, layout)
│   ├── account/                  # Django-allauth templates
│   ├── admin/                    # Custom admin templates
│   ├── cart/                     # Shopping cart templates
│   ├── core/                     # Core templates (contact page)
│   ├── home/                     # Home page template
│   ├── members/                  # Membership templates
│   ├── orders/                   # Order templates
│   ├── payment/                  # Checkout and payment templates
│   ├── products/                 # Product templates
│   └── profile/                  # User profile templates
│
├── media/                        # User-uploaded files (not in git)
│   ├── digital_products/         # Digital product files
│   ├── product_images/           # Product images
│   ├── product_audio/            # Product audio files
│   └── product_videos/           # Product video files
│
├── nginx/                        # Nginx configuration
│   └── nginx.conf                # Nginx reverse proxy config
│
├── tools/                        # Utility scripts
│   ├── backup_postgres.py        # Database backup script
│   ├── restore_postgres.py       # Database restore script
│   ├── test_db_connection.py     # Database connection test
│   └── README.md                 # Tools documentation
│
├── docs/                         # Documentation files
│   ├── AWS_DEPLOYMENT.md         # AWS EC2 deployment guide
│   ├── DOCKER_SETUP.md           # Docker setup guide
│   ├── NGINX_SETUP.md            # Nginx configuration guide
│   ├── HTTPS_SETUP.md            # SSL/HTTPS setup guide
│   ├── PICKUP_LOCATION_SETUP.md  # Pickup location feature guide
│   ├── EMAIL_VERIFICATION.md     # Email verification setup
│   ├── DATABASE_SETUP.md         # Database configuration
│   └── PROJECT_STRUCTURE.md      # This file
│
├── backups/                      # Database backups (not in git)
│
├── venv/                         # Python virtual environment (not in git)
│
├── .env                          # Environment variables (not in git)
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore rules
├── .dockerignore                 # Docker ignore rules
│
├── docker-compose.yml            # Development Docker Compose config
├── docker-compose.prod.yml      # Production Docker Compose config
├── Dockerfile                    # Docker image definition
│
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Poetry configuration (optional)
│
├── README.md                     # Main project README
└── [Various .md files]          # Additional documentation (being moved to docs/)
```

## 🔑 Key Files Explained

### Configuration Files

- **`fitness_club/fitness_club/settings.py`**: Main Django settings
  - Database configuration
  - Installed apps
  - Middleware
  - Static/media file settings
  - Email configuration
  - Security settings

- **`fitness_club/fitness_club/urls.py`**: Root URL configuration
  - Includes all app URLs
  - Health check endpoint
  - Media file serving (development)

- **`.env`**: Environment variables (not in git)
  - Secret keys
  - Database credentials
  - Debug mode
  - Allowed hosts

### Docker Files

- **`Dockerfile`**: Defines the web application container
- **`docker-compose.yml`**: Development multi-container setup
- **`docker-compose.prod.yml`**: Production setup with Nginx
- **`nginx/nginx.conf`**: Nginx reverse proxy configuration

### Models (Database Schema)

Key models across apps:

- **`products/models.py`**: Product, Category, ProductImage
- **`orders/models.py`**: Order, OrderItem, PickupLocation
- **`cart/models.py`**: CartItem
- **`profiles/models.py`**: UserProfile (shipping addresses)
- **`members/models.py`**: Membership models

### Views (Business Logic)

- **`payment/views.py`**: Checkout flow, order creation
- **`orders/views_orders.py`**: Order viewing and management
- **`products/views.py`**: Product listing and detail pages
- **`cart/views.py`**: Shopping cart operations

### Templates (User Interface)

- **`templates/base.html`**: Base template with navigation
- **`templates/payment/checkout.html`**: Checkout page
- **`templates/home/home.html`**: Home page with product listing
- **`templates/products/product_detail.html`**: Product detail page

## 📦 App Responsibilities

### accounts/
- User registration and login
- Email verification
- Password management
- Account settings

### cart/
- Add items to cart
- Update quantities
- Remove items
- Cart persistence (database)

### orders/
- Order creation
- Order management
- Digital download generation
- Pickup location management
- Order history

### payment/
- Checkout process
- Payment processing (simulated)
- Shipping calculation
- Tax calculation

### products/
- Product catalog
- Product categories
- Product images
- Inventory management
- Product types (physical/digital/service)

### profiles/
- User profile management
- Shipping address management
- Profile editing

### members/
- Membership tracking
- Membership management

### core/
- Shared utilities
- Contact page
- Admin customizations

## 🔄 Data Flow

1. **User Registration** → `accounts/` → Creates User and Profile
2. **Browse Products** → `products/` → `home/` displays products
3. **Add to Cart** → `cart/` → Stores CartItem in database
4. **Checkout** → `payment/` → Creates Order in `orders/`
5. **Order Processing** → `orders/services.py` → Generates downloads, sends emails
6. **View Orders** → `orders/views_orders.py` → Displays order history

## 🛠 Development Workflow

1. **Models**: Define in `app/models.py`
2. **Migrations**: `python manage.py makemigrations`
3. **Apply**: `python manage.py migrate`
4. **Admin**: Register in `app/admin.py`
5. **Views**: Create in `app/views.py`
6. **URLs**: Add routes in `app/urls.py`
7. **Templates**: Create in `templates/app/`
8. **Static**: Add to `static/` directory

## 📝 Notes

- All apps follow Django best practices
- Models use proper relationships (ForeignKey, ManyToMany)
- Views use proper authentication decorators
- Templates extend base.html for consistency
- Static files are organized by type (css, js)
- Media files are organized by purpose (product_images, digital_products)

