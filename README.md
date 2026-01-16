# Online Fitness Store
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Django](https://img.shields.io/badge/Django-4.x-darkgreen)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![AWS](https://img.shields.io/badge/AWS-EC2-orange)
![Stripe](https://img.shields.io/badge/Payments-Stripe-6772E5)
![License](https://img.shields.io/badge/License-Proprietary-red)


A comprehensive Django-based e-commerce platform for selling fitness products, digital downloads, and services. Built with production-ready features including user authentication, product management, shopping cart, order processing, and AWS EC2 deployment.

## 🌐 Live Site

**Visit**: [https://your-domain.com/](https://your-domain.com/)

> **Note**: Email verification is required for all new user registrations.




## 📸 Screenshots

### Home Page
Public landing page with featured products and membership access.
![Home](screenshots/home.png)

### Product Listing
Search, category filters, and pagination for physical, digital, and service products.
![Products](screenshots/products.png)

### Product Detail
Detailed product view with media gallery, stock tracking, and add-to-cart.
![Product Detail](screenshots/product_detail.png)

### Shopping Cart
Cart management with tax calculation and shipping rules.
![Cart](screenshots/cart.png)

### Admin Dashboard
Django admin interface for managing products, orders, inventory, and memberships.
![Admin](screenshots/dashboard.png)



## 🚀 Features

### Product Management
- **Multiple Product Types**: Physical products, digital downloads, and services
- **Product Categories**: Organize products by category
- **Image & Media Support**: Product images, videos, and audio files
- **Inventory Management**: Track stock levels for physical products
- **Service Booking**: Manage service seats and availability

### User Features
- **User Authentication**: Sign up, login, logout with email verification
- **User Profiles**: Manage shipping addresses and account settings
- **Shopping Cart**: Add/remove items, update quantities
- **Order Management**: View order history and download digital products
- **Membership System**: Track user memberships and subscriptions

### Checkout & Payment
- **Flexible Checkout**: 
  - Physical products: Shipping or pickup options
  - Digital/Service products: Simplified checkout (no shipping required)
- **Pickup Locations**: Multiple pickup locations for local orders
- **Tax Calculation**: Automatic GST/HST calculation
- **Shipping Options**: Flat rate or free shipping over threshold

### Admin Features
- **Django Admin Panel**: Full CRUD operations for all models
- **Order Management**: View and manage orders with pickup location details
- **Product Administration**: Manage products, categories, and inventory
- **User Management**: View and manage user accounts

### Deployment
- **Docker Containerization**: Production-ready Docker setup
- **Nginx Reverse Proxy**: SSL/HTTPS support with automatic HTTP to HTTPS redirect
- **AWS EC2 Deployment**: Complete deployment guide for cloud hosting
- **Database**: PostgreSQL for production, SQLite for development

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/online-fitness-store-M.git
cd online-fitness-store-M

# Using Docker (recommended)
docker compose up -d

# Or local setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ec2.env.example .env
# Edit .env with your settings
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)

## 🛠 Tech Stack

### Backend
- **Django 5.0.2**: Web framework
- **PostgreSQL**: Production database
- **SQLite**: Development database
- **Django Allauth**: Authentication and account management
- **Django REST Framework**: API support (optional)

### Frontend
- **HTML5/CSS3**: Responsive design
- **JavaScript**: Dynamic form interactions
- **Bootstrap-inspired**: Custom styling

### DevOps
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy and static file serving
- **Gunicorn**: WSGI HTTP server
- **AWS EC2**: Cloud hosting

## 🏗️ Architecture

### System Design
- **MVC Pattern**: Django follows Model-View-Template architecture
- **Database Design**: Normalized schema with proper relationships and foreign keys
- **Session Management**: Anonymous cart support with session-based storage that transfers to database on login
- **Security**: CSRF protection, SQL injection prevention, XSS protection, secure password hashing
- **Scalability**: Docker containerization, Nginx reverse proxy, static file optimization with WhiteNoise

### Technical Highlights
- **Anonymous Cart**: Session-based cart for non-authenticated users, seamlessly transfers to database cart upon login using Django signals
- **Dynamic Checkout**: Conditional checkout flow that adapts based on product types (shipping for physical, instant for digital/services)
- **Media Management**: Multi-image support with main image selection and media gallery
- **Featured Products**: Admin-configurable featured products with singleton pattern for content management
- **Search & Filtering**: Full-text search with category filtering and pagination
- **Context Processors**: Global cart item count available across all templates

## 📁 Project Structure

```
online-fitness-store/
├── accounts/              # User authentication and account management
├── api/                   # REST API endpoints (optional)
├── cart/                  # Shopping cart functionality
├── core/                  # Core utilities and shared functionality
├── fitness_club/          # Main Django project settings
│   └── fitness_club/      # Settings, URLs, WSGI/ASGI configs
├── home/                  # Home page and landing
├── members/               # Membership management
├── orders/                # Order processing and management
├── payment/               # Checkout and payment processing
├── products/              # Product catalog and management
├── profiles/              # User profile management
├── static/                # Static files (CSS, JS, images)
├── templates/             # HTML templates
├── media/                 # User-uploaded files (product images, digital files)
├── nginx/                 # Nginx configuration
├── tools/                 # Utility scripts (backup, restore, diagnostics)
├── docs/                  # Documentation files
├── docker-compose.yml     # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Key Apps Explained

- **accounts/**: Handles user registration, login, email verification, and account settings
- **cart/**: Shopping cart models and views for adding/removing items
- **orders/**: Order models, order processing, digital download management, pickup locations
- **payment/**: Checkout flow, payment processing (simulated), order creation
- **products/**: Product catalog, categories, inventory management, product types (physical/digital/service)
- **profiles/**: User profile management, shipping addresses
- **members/**: Membership tracking and management
- **core/**: Shared utilities, admin customizations, contact page

## 🚀 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- Docker & Docker Compose (optional, for containerized deployment)
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/online-fitness-store-M.git
   cd online-fitness-store-M
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp ec2.env.example .env
   ```
   
   Edit `.env` with your settings:
   ```env
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=1
   POSTGRES_DB=fitness_club_db
   POSTGRES_USER=fitness_user
   POSTGRES_PASSWORD=your-password
   DB_HOST=localhost
   POSTGRES_PORT=5432
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

   Visit `http://localhost:8000` in your browser.

### Docker Setup (Recommended)

See [docs/setup/DOCKER_SETUP.md](docs/setup/DOCKER_SETUP.md) for detailed Docker setup instructions.

## ⚙️ Configuration

### Environment Variables

Key environment variables (set in `.env` file):

- `DJANGO_SECRET_KEY`: Secret key for Django (required)
- `DJANGO_DEBUG`: Set to `1` for development, `0` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `DB_HOST`: Database host (use `db` for Docker, `localhost` for local)
- `POSTGRES_PORT`: Database port (default: 5432)

### Django Settings

Main settings file: `fitness_club/fitness_club/settings.py`

Key configurations:
- **Database**: PostgreSQL for production, SQLite for development
- **Static Files**: Served via WhiteNoise in production
- **Media Files**: Served via Nginx in production
- **Email**: Configured for email verification (see [docs/setup/EMAIL_VERIFICATION.md](docs/setup/EMAIL_VERIFICATION.md))
- **Authentication**: Django Allauth for user management

## 💻 Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Admin Panel

1. Create a superuser (if not already created):
   ```bash
   python manage.py createsuperuser
   ```

2. Visit `http://localhost:8000/admin/` and login

### Key Development Commands

```bash
# Collect static files
python manage.py collectstatic

# Create a new app
python manage.py startapp app_name

# Open Django shell
python manage.py shell

# Check for issues
python manage.py check
```

## 🚢 Deployment

### AWS EC2 Deployment

Complete deployment guide: [docs/deployment/AWS_DEPLOYMENT.md](docs/deployment/AWS_DEPLOYMENT.md)

Quick steps:
1. Set up EC2 instance
2. Install Docker and Docker Compose
3. Clone repository
4. Configure environment variables
5. Set up Nginx reverse proxy
6. Configure SSL/HTTPS
7. Deploy with Docker Compose

### Production Checklist

- [ ] Set `DJANGO_DEBUG=0` in `.env`
- [ ] Set strong `DJANGO_SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure email backend for production
- [ ] Set up database backups
- [ ] Configure static file serving
- [ ] Set up monitoring and logging

## 📚 Documentation

All documentation is organized in the `docs/` folder. See [docs/README.md](docs/README.md) for a complete index.

**Quick Links:**
- **[Project Structure](docs/PROJECT_STRUCTURE.md)**: Detailed project organization and file structure
- **[Code Documentation](docs/CODE_DOCUMENTATION.md)**: Code documentation guide and standards
- **[AWS Deployment](docs/deployment/AWS_DEPLOYMENT.md)**: Complete AWS EC2 deployment guide
- **[Docker Setup](docs/setup/DOCKER_SETUP.md)**: Docker setup and configuration
- **[Nginx Setup](docs/setup/NGINX_SETUP.md)**: Nginx reverse proxy configuration
- **[HTTPS Setup](docs/setup/HTTPS_SETUP.md)**: SSL/HTTPS setup guide
- **[Pickup Location Setup](docs/setup/PICKUP_LOCATION_SETUP.md)**: Pickup location feature guide
- **[Email Verification](docs/setup/EMAIL_VERIFICATION.md)**: Email verification setup
- **[Database Setup](docs/setup/DATABASE_SETUP.md)**: Database configuration

**Organized Documentation:**
- **[Deployment Guides](docs/deployment/)**: All deployment-related documentation
- **[Setup Guides](docs/setup/)**: Configuration and setup instructions
- **[User Guides](docs/guides/)**: Testing, migration, and feature guides

## 🎯 Key Features Implementation

### Product Types

The system supports three product types:

1. **Physical Products**: Require shipping or pickup
   - Stock management
   - Shipping cost calculation
   - Pickup location selection

2. **Digital Products**: Instant download
   - File or URL-based delivery
   - Download link generation with expiry
   - Email delivery

3. **Service Products**: Bookable services
   - Seat management
   - Date/time scheduling
   - Location information

### Checkout Flow

- **Physical Products**: Shows shipping/pickup options and address form
- **Digital/Service Only**: Simplified checkout (order summary only)
- **Mixed Cart**: Full checkout with shipping options

### Order Processing

1. User adds items to cart
2. Proceeds to checkout
3. Selects fulfillment method (shipping/pickup for physical products)
4. Places order
5. Order created with status "paid" (simulated payment)
6. Digital products: Download links generated and emailed
7. Services: Seats deducted from availability


## 🙏 Acknowledgments

Built with Django, Docker, and modern web technologies. Special thanks to the Django community for excellent documentation and tools.

## 📞 Support

For questions or issues:
- Check the [documentation](docs/) folder
- Review the code comments (extensively documented)
- Open an issue on GitHub

---

**Note**: This platform is production-ready and includes comprehensive error handling, security best practices, and deployment configurations.

