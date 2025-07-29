# Cafe24 POS - Frontend (PWA)

This is the React-based Progressive Web Application (PWA) frontend for the Cafe24 Point of Sale system.

## Overview

The frontend provides a modern, responsive interface for different user roles:
- **Manager Dashboard**: Complete system administration
- **Cashier Interface**: Order management and payment processing  
- **Barista Dashboard**: Order preparation workflow
- **Courier Interface**: Delivery management

## Technology Stack

- **React 19.x**: Modern React with hooks and context
- **Material-UI 7.x**: Component library and design system
- **Axios**: HTTP client for API communication
- **PWA Features**: Service worker for offline capability

## Quick Start

### Prerequisites
- Node.js 14+ and npm
- Backend API running on `http://localhost:5000`

### Development Setup
```bash
cd pwa_frontend
npm install
npm start
```

The app runs on [http://localhost:3000](http://localhost:3000)

### Environment Configuration
Create a `.env` file:
```
REACT_APP_API_URL=http://localhost:5000
```

### Testing
```bash
npm test
```

### Production Build
```bash
npm run build
```

## Features

### Authentication & Authorization
- JWT-based authentication
- Role-based routing and access control
- Secure token management

### Manager Dashboard
- Menu item management (CRUD operations)
- Category organization
- User management
- Sales reports and analytics
- System settings configuration

### Cashier Interface  
- Order creation and management
- Menu browsing with categories
- Payment processing
- Customer management

### Barista Dashboard
- Active orders queue
- Order preparation tracking
- Status updates
- Kitchen workflow management

### Courier Interface
- Delivery order management
- Route optimization
- Delivery status tracking
- Completion reporting

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── MenuManager.js   # Menu item management
│   ├── OrderPlacement.js # Order creation interface
│   ├── ReportsManager.js # Analytics and reports
│   └── StockManager.js  # Inventory management
├── DashboardManager.js  # Manager dashboard
├── DashboardCashier.js  # Cashier interface
├── DashboardBarista.js  # Barista dashboard
├── DashboardCourier.js  # Courier interface
├── Login.js            # Authentication component
└── App.js              # Main application component
```

## API Integration

The frontend communicates with the Flask backend via REST API:
- **Base URL**: `REACT_APP_API_URL` environment variable
- **Authentication**: JWT tokens in Authorization header
- **Data Format**: JSON requests/responses

### Key API Endpoints
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/menu-items` - Fetch menu items
- `POST /api/v1/orders` - Create new orders
- `GET /api/v1/orders/active` - Get active orders
- `PUT /api/v1/orders/{id}/status` - Update order status

## Development Guidelines

### Code Style
- Use functional components with hooks
- Follow Material-UI design patterns
- Implement responsive design principles
- Use ESLint configuration for code consistency

### State Management
- React hooks (useState, useEffect, useContext)
- Local component state for UI state
- API calls with proper error handling

### Testing
- Jest and React Testing Library
- Component unit tests
- Integration tests for key workflows

## PWA Features

- **Service Worker**: Offline capability and caching
- **Manifest**: App installation support
- **Responsive Design**: Mobile-first approach
- **Performance**: Optimized loading and rendering

## Security

- JWT token validation
- Role-based UI rendering
- Secure API communication
- Input validation and sanitization

## Deployment

### Production Build
```bash
npm run build
```

### Static Hosting
Deploy the `build/` folder to any static hosting service:
- Nginx
- Apache
- Netlify  
- Vercel
- AWS S3 + CloudFront

### Environment Variables
Configure production environment:
```
REACT_APP_API_URL=https://your-api-domain.com
```

## Troubleshooting

### Common Issues

**Build Warnings**
- Unused variables: Remove or prefix with underscore
- Missing dependencies: Add to useEffect dependency arrays
- ESLint errors: Follow the suggested fixes

**API Connection Issues**
- Verify REACT_APP_API_URL is correct
- Check CORS configuration on backend
- Ensure backend is running and accessible

**Authentication Problems**  
- Clear localStorage and reload
- Check token expiration
- Verify backend JWT configuration

## Browser Support

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Contributing

1. Follow the existing code structure
2. Add tests for new components
3. Update documentation as needed
4. Follow Material-UI design guidelines
5. Ensure responsive design compliance

For more details, see the main project README in the repository root.
