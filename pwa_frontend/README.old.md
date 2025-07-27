# PWA Frontend for Coffee Shop POS - v0.1

This directory will contain the Progressive Web Application (PWA) frontend for the Coffee Shop POS system.

## Technology Choice

To be built with a modern JavaScript framework such as:
*   **React** (with Create React App, Vite, or Next.js)
*   **Vue.js** (with Vue CLI or Vite)
*   **Angular** (with Angular CLI)

The specific choice can be made by the development team based on expertise and project requirements.

## Conceptual Structure (v0.1 - Expanded Scope)

The PWA will be a Single Page Application (SPA) with the following key components and views:

### I. Overall PWA Structure & Shared Elements:

*   **Root Component (`App`):**
    *   Manages global layout, routing, and authentication state.
    *   Conditionally renders `LoginPage` or the main `DashboardLayout` based on auth status.
*   **Router:**
    *   Defines routes for `/login`, `/courier`, `/barista`, `/cashier`, `/manager` (and sub-routes like `/manager/menu`, `/manager/sales`).
    *   Protected routes that require authentication and potentially role checks before allowing access.
*   **Authentication Service/Store (`AuthService` / `AuthContext` / `AuthStore`):**
    *   Handles login/logout actions (making API calls to the backend).
    *   Stores the JWT token (e.g., in localStorage or a secure cookie) and logged-in user information (ID, username, role, full name).
    *   Provides authentication status and user data to other components.
*   **API Service (`ApiService`):**
    *   A centralized module/service for making all API calls to the Python backend.
    *   Includes functions like `loginUser(credentials)`, `fetchActiveMenu()`, `submitOrder(orderData)`, `getBaristaOrders()`, `updateOrderStatus(orderId, statusUpdateData)`, `getOrderByNumber(orderNum)`, `getCategories()`, `addCategory(categoryData)`, `getMenuItems()`, `addMenuItem(itemData)`, `getDailySalesSummary()`.
    *   Automatically attaches the JWT token to authorization headers for protected endpoints.
    *   Handles basic error catching from API calls.
*   **Shared UI Components:**
    *   `NavbarComponent`: Displays the application title, current logged-in user's name/role, and a logout button. May also contain primary navigation links for the Manager role.
    *   `LoadingSpinnerComponent`: A visual indicator for when data is being fetched.
    *   `ErrorMessageComponent`: A standardized way to display error messages to the user.
    *   `ResponsiveLayoutComponent`: Ensures content adapts to different screen sizes (tablet, PC).

### II. Role-Specific Dashboard/View Components (v0.1):

1.  **`LoginPage` View Component:**
    *   Inputs for username and password.
    *   "Login" button.
    *   On submit, calls `AuthService.login()`.
    *   Displays validation errors or API error messages.
    *   On successful login, redirects to the appropriate role-based dashboard.

2.  **`CourierDashboardView` Component (Tablet-Optimized):**
    *   **`MenuDisplayComponent`:**
        *   Fetches and displays the active menu from `ApiService`.
        *   Groups items by category.
        *   Shows item name, LBP price (rounded), USD price (reference).
        *   Allows selection of pre-loaded options (e.g., sizes) which may affect price.
        *   Action: Adds selected item/option configuration to the order cart.
    *   **`OrderCartComponent`:**
        *   Displays items currently in the order (name, selected option, quantity, line total LBP/USD).
        *   For v0.1: Quantity defaults to 1. Simple "Remove Item" button.
        *   Displays order subtotal.
    *   **`CustomerNumberInputComponent`:** Text input for the customer's number/identifier.
    *   **`SubmitOrderButtonComponent`:**
        *   Collects cart data and customer number.
        *   Calls `ApiService.submitOrder()`.
        *   On success: Clears the cart, shows a success message (e.g., "Order [number] created!").
        *   On failure: Shows an error message.

3.  **`BaristaDashboardView` Component (Tablet-Optimized):**
    *   **`BaristaOrderListComponent`:**
        *   Fetches and displays orders relevant to the barista (e.g., statuses `paid_waiting_preparation`, `preparing`) from `ApiService.getBaristaOrders()`.
        *   Uses polling for v0.1 to refresh the list (WebSockets for future enhancement).
        *   Displays orders as cards or list items: Order Number, brief items summary, Customer Number, Status (visually distinct, e.g., color-coded).
        *   Orders should be sorted, typically by creation time (oldest first).
    *   **`OrderCardActionsComponent` (part of each order display):**
        *   "Start Preparation" button: Enabled if status is `paid_waiting_preparation`. Calls `ApiService.updateOrderStatus(orderId, 'preparing')`.
        *   "Order Ready" button: Enabled if status is `preparing`. Calls `ApiService.updateOrderStatus(orderId, 'ready_for_pickup')`.

4.  **`CashierDashboardView` Component (PC-Optimized):**
    *   **`OrderLookupFormComponent`:**
        *   Input field for Order Number.
        *   "Find Order" button. Calls `ApiService.getOrderByNumber()`.
    *   **`OrderDetailsDisplayComponent`:**
        *   Displays details of the fetched order: items, options, quantities, total LBP/USD, current status.
    *   **`MarkAsPaidButtonComponent`:**
        *   Enabled if order status is `pending_payment`.
        *   Calls `ApiService.updateOrderStatus(orderId, 'paid_waiting_preparation', { payment_method: 'simulated_cash' })`.
        *   Shows success/error message.

5.  **`ManagerDashboardView` Component (PC/Tablet Optimized):**
    *   Main layout with navigation to different manager sections.
    *   **`ManagerMenuAdminView` Sub-View Component:**
        *   `CategoryDisplayListComponent`: Displays list of categories. Has "Add Category" button.
        *   `AddCategoryFormComponent` (Modal or separate section): Form for new category name and sort order. Submits to `ApiService.addCategory()`.
        *   `MenuItemDisplayListComponent`: Displays list of menu items. Has "Add Menu Item" button.
        *   `AddMenuItemFormComponent` (Modal or separate section): Form for new simple item (name, category dropdown, USD price, description). Submits to `ApiService.addMenuItem()`.
    *   **`ManagerDailySalesView` Sub-View Component:**
        *   Fetches data from `ApiService.getDailySalesSummary()`.
        *   Displays a table/list of today's orders (Order #, Customer #, Final LBP Total, Status).
        *   Displays a summary: "Today's Total Sales (LBP): [calculated_amount]".

### State Management Considerations for v0.1:

*   **Global State:** Logged-in user details, JWT token, possibly cached active menu data.
*   **Local/Component State:** Courier's current order cart, list of orders for Barista, details of the order being viewed by Cashier, data for manager views.

This structure provides a starting point. The actual file names and component granularity will depend on the chosen JavaScript framework and developer preferences.
```
