# API Setup Guide

This guide explains how to set up and use the REST API for the Fitness Store.

## Installation Steps

### 1. Verify Installation

Django REST Framework is already installed. Token authentication is built into DRF, so no separate package is needed.

To verify:
```bash
pip list | grep djangorestframework
# Should show: djangorestframework
```

### 2. Run Migrations (Already Completed)

The migrations have already been run, which created the `authtoken_token` table for storing API tokens.

If you need to run migrations again:
```bash
python manage.py migrate
```

## API Endpoints

### Product Endpoints

#### List All Products
```
GET /api/products/
```

**Query Parameters:**
- `category` - Filter by category ID
- `seller` - Filter by seller ID
- `is_digital` - Filter digital products (true/false)
- `is_service` - Filter service products (true/false)
- `featured` - Show only featured products (true/false)
- `q` - Search query (searches name and description)

**Example:**
```
GET /api/products/?category=1&featured=true
GET /api/products/?q=yoga
```

#### Get Product Details
```
GET /api/products/{id}/
```

#### Get Featured Products
```
GET /api/products/featured/
```

#### Search Products
```
GET /api/products/search/?q=query
```

### Category Endpoints

#### List All Categories
```
GET /api/categories/
```

#### Get Category Details
```
GET /api/categories/{id}/
```

## Authentication

### Token Authentication

To access protected endpoints (if you add them later), you need to obtain an authentication token.

#### Get Token

Send a POST request to:
```
POST /api/auth/token/
```

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "token": "example_token_1234567890abcdef"
}
```

**Note:** This is just an example. Each user gets a unique token when they authenticate.

#### Using the Token

Include the token in the `Authorization` header:
```
Authorization: Token example_token_1234567890abcdef
```

**Important:** Replace `example_token_1234567890abcdef` with the actual token you receive from the API.

## Example API Usage

### Using cURL

```bash
# List all products
curl http://localhost:8000/api/products/

# Get product details
curl http://localhost:8000/api/products/1/

# Search products
curl http://localhost:8000/api/products/search/?q=yoga

# Get featured products
curl http://localhost:8000/api/products/featured/

# Get token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### Using Python requests

```python
import requests

# List products
response = requests.get('http://localhost:8000/api/products/')
products = response.json()

# Get token
token_response = requests.post(
    'http://localhost:8000/api/auth/token/',
    json={'username': 'your_username', 'password': 'your_password'}
)
token = token_response.json()['token']

# Use token for authenticated requests
headers = {'Authorization': f'Token {token}'}
response = requests.get('http://localhost:8000/api/products/', headers=headers)
```

**Note:** The `token` variable contains the actual token received from the API, not the example value shown above.
```

### Using JavaScript/Fetch

```javascript
// List products
fetch('http://localhost:8000/api/products/')
  .then(response => response.json())
  .then(data => console.log(data));

// Get token
fetch('http://localhost:8000/api/auth/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
})
  .then(response => response.json())
  .then(data => {
    const token = data.token; // Actual token from API response
    // Use token for authenticated requests
    fetch('http://localhost:8000/api/products/', {
      headers: {
        'Authorization': `Token ${token}`
      }
    })
      .then(response => response.json())
      .then(data => console.log(data));
  });
```

## Response Format

All API responses follow REST conventions:

### List Response
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Yoga Mat",
      "price": "29.99",
      "description": "...",
      "is_active": true,
      ...
    }
  ]
}
```

### Detail Response
```json
{
  "id": 1,
  "name": "Yoga Mat",
  "price": "29.99",
  "description": "...",
  "is_active": true,
  "category": {
    "id": 1,
    "name": "Equipment",
    "slug": "equipment"
  },
  "images": [...],
  "main_image_url": "http://localhost:8000/media/product_images/yoga_mat.jpg",
  ...
}
```

## Configuration

The API is configured in `settings.py`:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
```

## Next Steps

1. **Add more endpoints**: You can add API endpoints for Orders, Cart, Memberships, etc.
2. **Add write permissions**: Currently all endpoints are read-only. Add write permissions for authenticated users.
3. **Add filtering**: Enhance filtering options (price range, date range, etc.)
4. **Add rate limiting**: Protect your API from abuse
5. **Add API documentation**: Use drf-spectacular or drf-yasg for automatic API documentation

## Files Created

- `products/serializers.py` - Serializers for Product and Category models
- `products/api_views.py` - API ViewSets for products and categories
- `products/api_urls.py` - URL routing for API endpoints
- `fitness_club/fitness_club/settings.py` - REST Framework configuration
- `fitness_club/fitness_club/urls.py` - Main URL configuration with API routes

