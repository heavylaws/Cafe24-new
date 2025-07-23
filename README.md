# Coffee Shop POS System (Local Deployment) - v0.2

## 1. Project Overview

This project is Version 0.2 of a Point of Sale (POS) system designed for a fast-paced coffee shop environment. It now features a robust, JWT-protected Flask backend and a modern React PWA frontend, with a focus on clear API conventions and maintainable, future-proof code. The workflow supports parallel backend/frontend development with synchronized file access.

## 2. Key Features (v0.2 - Major Updates)

*   **Menu Management (Manager UI):**
    *   Fully rewritten MenuManager component in React.
    *   All API calls use `/api/v1/menu-items` and `/api/v1/categories` endpoints.
    *   JWT Authorization header is included in every request.
    *   Data model fields match backend: `base_price_usd`, `is_active`, etc.
    *   Modern, responsive UI with robust CRUD operations for menu items.
    *   **Category management now supports add, edit, and delete.**
    *   **Menu item options/choices management UI is coming soon.**
*   **Backend Improvements:**
    *   All endpoints expect JWT-based authentication and role-based access.
    *   Consistent data model and endpoint structure.
    *   New endpoint `/api/v1/ingredients/<id>/usage` lists menu items using an ingredient.
*   **Workflow:**
    *   Parallel development: backend (Flask, in `app/`) and frontend (React, in `pwa_frontend/`).
    *   Editors (Cursor for backend, Windsurf for frontend) work on the same local files for instant updates.
    *   All changes are committed to GitHub for seamless collaboration and migration between machines.

## 3. Technology Stack

*   **Backend:** Python (Flask), PostgreSQL/MySQL, JWT, SQLAlchemy
*   **Frontend:** React (PWA), Axios, Modern CSS
*   **API:** RESTful, JWT-protected, versioned endpoints

## 4. System Architecture Overview

1.  **PWA Frontend:** Single codebase for all roles, robust Manager dashboard for menu and category management.
2.  **Python Backend API:** Handles business logic, authentication, and data persistence.
3.  **Database Server:** Stores all persistent data.
4.  **Local Network:** All devices communicate over local network.

## 5. Getting Started

### Backend Setup

1.  See previous instructions (unchanged).

### Frontend PWA Setup

1.  See previous instructions (unchanged).
2.  To launch the React development server, navigate to `pwa_frontend` and run `npm start`.
3.  Ensure your `.env` file in `pwa_frontend/` sets `REACT_APP_API_URL` to your backend server address.

### MenuManager Component (Frontend)

*   Located at `pwa_frontend/src/components/MenuManager.js`.
*   Uses correct endpoints and JWT headers for all CRUD operations.
*   Data model fields: `name`, `description`, `base_price_usd`, `category_id`, `is_active`.
*   UI is modern, responsive, and robust.
*   **Menu item options/choices management UI is coming soon.**

### CategoryManager Component (Frontend)

*   Located at `pwa_frontend/src/components/CategoryManager.js`.
*   Supports adding, editing, and deleting categories.
*   To add a category: Fill in the name (and optional sort order) and click "Add Category".
*   To edit a category: Click "Edit" next to a category, modify the fields, and click "Save".
*   To delete a category: Click "Delete" and confirm the action.

## 6. Workflow & Collaboration

*   Use Cursor for backend (`app/`), Windsurf for frontend (`pwa_frontend/`).
*   All changes are committed and pushed to GitHub.

## 7. Manual Tests

Example scripts for local API testing now live in `manual_tests/`. They require
a running instance of the application and are excluded from automated test runs.

## 8. What's Next

*   Expand Manager dashboard to support options and choices.
*   Add more robust error handling and user feedback.
*   Continue to keep backend and frontend in sync with data model and endpoint conventions.

---
This README is up to date as of v0.2.
See [docs/last_9_tasks.md](docs/last_9_tasks.md) for a summary of recent tasks.
