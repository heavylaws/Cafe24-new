# Cafe24 POS System (Local Deployment) - v1.0

## 1. Project Overview

Cafe24 is a comprehensive Point of Sale (POS) system designed for modern cafe and restaurant environments. This production-ready system features a robust JWT-protected Flask backend and a modern React Progressive Web App (PWA) frontend. The system is built with scalability, security, and user experience in mind, supporting multiple user roles and a complete order management workflow.

## 2. Key Features

### Core Functionality
- **Multi-role System**: Supports Managers, Cashiers, Baristas, and Couriers with role-based access control
- **Order Management**: Complete order lifecycle from creation to completion
- **Menu Management**: Full CRUD operations for menu items, categories, and ingredients
- **Inventory Tracking**: Real-time ingredient usage and stock level monitoring
- **Reporting**: Sales analytics and business insights

### Order Workflow
1. **Order Creation**: Cashiers create new orders with items and customizations
2. **Payment Processing**: Mark orders as paid with support for multiple payment methods
3. **Order Preparation**: Baristas view and update order status during preparation
4. **Order Fulfillment**: Couriers mark orders as ready for pickup or delivered
5. **Completion**: Orders are archived with complete transaction history

### Technical Highlights
- **Backend**: Python (Flask), SQLite (production-ready with PostgreSQL support)
- **Frontend**: React PWA with Material-UI for responsive design
- **Authentication**: JWT-based authentication with role-based access control
- **API**: RESTful endpoints with consistent error handling and validation

## 3. System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React PWA      │ ◄──►│  Flask API      │ ◄──►│  SQLite/        │
│  (Frontend)     │     │  (Backend)      │     │  PostgreSQL     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 4. Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   python init_db.py
   ```
5. Start the development server:
   ```bash
   python run.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd pwa_frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file with:
   ```
   REACT_APP_API_URL=http://localhost:5000
   ```
4. Start the development server:
   ```bash
   npm start
   ```

## 5. User Roles

### Manager
- Full system access
- Menu and inventory management
- User management
- Reporting and analytics

### Cashier
- Create and manage orders
- Process payments
- View order status

### Barista
- View active orders
- Update order preparation status
- Manage drink preparation queue

### Courier
- View orders ready for delivery
- Update delivery status
- Mark orders as completed

## 6. API Documentation

The API follows RESTful conventions and is versioned under `/api/v1/`. All endpoints require JWT authentication.

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### Orders
- `GET /api/v1/orders` - List all orders
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders/active` - Get active orders
- `PUT /api/v1/orders/{id}/status` - Update order status

## 7. Development Workflow

1. **Backend Development**: Work in the `app/` directory
2. **Frontend Development**: Work in the `pwa_frontend/` directory
3. **Database Migrations**: Use Alembic for schema changes
4. **Testing**: Run tests with `pytest`

## 8. Deployment

### Production Requirements
- Gunicorn or uWSGI for production server
- PostgreSQL for production database
- Nginx as reverse proxy
- Environment variables for configuration

### Environment Variables
```
FLASK_APP=run.py
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

## 9. Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 10. License

This project is licensed under the MIT License - see the LICENSE file for details.

## 11. Future Enhancements

- Real-time order updates with WebSockets
- Mobile app for couriers
- Advanced reporting and analytics
- Integration with payment gateways
- Customer loyalty program

---
This README is up to date as of v1.0
