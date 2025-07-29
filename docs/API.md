# Cafe24 POS - API Documentation

## Overview

The Cafe24 POS system provides a comprehensive REST API for managing a point-of-sale system for coffee shops and restaurants.

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication

All API endpoints (except login) require JWT authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "user": {
    "id": "integer",
    "username": "string", 
    "full_name": "string",
    "role": "string"
  }
}
```

## Menu Management

### Get Menu Items
```http
GET /menu-items
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Espresso",
    "description": "Rich and bold espresso",
    "base_price_usd": 2.50,
    "price_lbp_rounded": 225000,
    "category_id": 1,
    "category_name": "Hot Drinks",
    "is_active": true,
    "image_url": "string",
    "options": []
  }
]
```

### Create Menu Item
```http
POST /menu-items
```

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "base_price_usd": "decimal",
  "category_id": "integer",
  "is_active": true,
  "image_url": "string"
}
```

### Update Menu Item
```http
PUT /menu-items/{id}
```

### Delete Menu Item
```http
DELETE /menu-items/{id}
```

## Category Management

### Get Categories
```http
GET /categories
```

### Create Category
```http
POST /categories
```

**Request Body:**
```json
{
  "name": "string",
  "sort_order": "integer"
}
```

## Order Management

### Get Orders
```http
GET /orders
```

**Query Parameters:**
- `status`: Filter by order status
- `user_id`: Filter by user

### Get Active Orders
```http
GET /orders/active
```

### Create Order
```http
POST /orders
```

**Request Body:**
```json
{
  "customer_number": "string",
  "items": [
    {
      "menu_item_id": "integer",
      "quantity": "integer",
      "chosen_option_choice_id": "integer"
    }
  ]
}
```

### Update Order Status
```http
PUT /orders/{id}/status
```

**Request Body:**
```json
{
  "status": "pending|preparation|ready|delivered|cancelled"
}
```

## Inventory Management

### Get Ingredients
```http
GET /ingredients
```

### Create Ingredient
```http
POST /ingredients
```

### Update Stock
```http
PUT /stock/{ingredient_id}
```

**Request Body:**
```json
{
  "quantity_change": "decimal",
  "adjustment_type": "restock|waste|consumption",
  "notes": "string"
}
```

## Reports

### Sales Report
```http
GET /reports/sales
```

**Query Parameters:**
- `start_date`: ISO date string
- `end_date`: ISO date string
- `user_id`: Filter by user

### User Performance
```http
GET /reports/user-performance
```

### Inventory Report
```http
GET /reports/inventory
```

## System Settings

### Get Settings
```http
GET /system-settings
```

### Update Settings
```http
PUT /system-settings
```

**Request Body:**
```json
{
  "usd_to_lbp_exchange_rate": "decimal",
  "primary_currency_code": "string",
  "secondary_currency_code": "string"
}
```

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Validation error",
  "message": "Detailed error message",
  "details": {}
}
```

### 401 Unauthorized
```json
{
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "message": "Internal server error"
}
```

## Role-Based Access Control

### Manager Role
- Full access to all endpoints
- User management
- System settings
- All reports

### Cashier Role
- Menu items (read-only)
- Orders (create, update status)
- Customer management

### Barista Role
- Active orders (read)
- Order status updates (preparation, ready)

### Courier Role
- Delivery orders (read)
- Order status updates (delivered)

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response Headers:**
- `X-Total-Count`: Total number of items
- `X-Page`: Current page
- `X-Per-Page`: Items per page

## Data Formats

### Dates
All dates are in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

### Currencies
- USD amounts: Decimal with 2 decimal places
- LBP amounts: Integer (rounded to nearest 5000)

### Status Values

**Order Status:**
- `pending`: Order created, awaiting preparation
- `preparation`: Order being prepared
- `ready`: Order ready for pickup/delivery
- `delivered`: Order completed
- `cancelled`: Order cancelled

**User Roles:**
- `manager`: Full system access
- `cashier`: Order management
- `barista`: Order preparation
- `courier`: Delivery management

## Webhooks

The system supports webhooks for real-time updates:

### Order Status Changes
```http
POST {webhook_url}
```

**Payload:**
```json
{
  "event": "order.status_changed",
  "data": {
    "order_id": "integer",
    "old_status": "string",
    "new_status": "string",
    "timestamp": "string"
  }
}
```

## SDKs and Libraries

### JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Python
```python
import requests

class Cafe24API:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_menu_items(self):
        response = requests.get(
            f'{self.base_url}/menu-items',
            headers=self.headers
        )
        return response.json()
```

## Testing

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### API Testing with curl
```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "manager1", "password": "password123"}'

# Get menu items
curl -X GET http://localhost:5000/api/v1/menu-items \
  -H "Authorization: Bearer <token>"
```

## Support

For API support and questions:
- Check the main project documentation
- Review the source code in the `app/routes/` directory
- Create an issue in the project repository