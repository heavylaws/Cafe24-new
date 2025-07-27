-- Coffee Shop POS - v0.1 Database Schema (PostgreSQL)

-- System Settings Table
CREATE TABLE SystemSettings (
    setting_key VARCHAR(255) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users Table
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('courier', 'cashier', 'barista', 'manager')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Categories Table
CREATE TABLE Categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Menu Items Table
CREATE TABLE MenuItems (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES Categories(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price_usd DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    image_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (category_id, name)
);

-- MenuItemOptions Table
CREATE TABLE MenuItemOptions (
    id SERIAL PRIMARY KEY,
    menu_item_id INTEGER NOT NULL REFERENCES MenuItems(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., 'Size'
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (menu_item_id, name)
);

-- MenuItemOptionChoices Table
CREATE TABLE MenuItemOptionChoices (
    id SERIAL PRIMARY KEY,
    menu_item_option_id INTEGER NOT NULL REFERENCES MenuItemOptions(id) ON DELETE CASCADE,
    choice_name VARCHAR(100) NOT NULL, -- e.g., 'Small', 'Medium'
    price_usd DECIMAL(10, 2) NOT NULL, -- Absolute price for this item variant
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (menu_item_option_id, choice_name)
);

-- Orders Table
CREATE TABLE Orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    courier_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE RESTRICT,
    cashier_id INTEGER REFERENCES Users(id) ON DELETE RESTRICT,
    barista_id INTEGER REFERENCES Users(id) ON DELETE RESTRICT,
    customer_number VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_payment' CHECK (status IN ('pending_payment', 'paid_waiting_preparation', 'preparing', 'ready_for_pickup', 'completed', 'cancelled_by_user', 'cancelled_by_staff')),
    final_total_usd DECIMAL(10,2) NOT NULL,
    final_total_lbp_rounded INTEGER NOT NULL,
    exchange_rate_at_order_time DECIMAL(10,4) NOT NULL,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_status ON Orders(status);
CREATE INDEX idx_orders_created_at ON Orders(created_at);
CREATE INDEX idx_orders_courier_id ON Orders(courier_id);
CREATE INDEX idx_orders_cashier_id ON Orders(cashier_id);

-- OrderItems Table
CREATE TABLE OrderItems (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES Orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER NOT NULL REFERENCES MenuItems(id) ON DELETE RESTRICT,
    menu_item_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    chosen_option_choice_id INTEGER REFERENCES MenuItemOptionChoices(id),
    chosen_option_choice_name VARCHAR(100),
    unit_price_usd_at_order DECIMAL(10, 2) NOT NULL,
    unit_price_lbp_rounded_at_order INTEGER NOT NULL,
    line_total_usd_at_order DECIMAL(10,2) NOT NULL,
    line_total_lbp_rounded_at_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Initial System Settings Data for v0.1
INSERT INTO SystemSettings (setting_key, setting_value) VALUES ('usd_to_lbp_exchange_rate', '90000');
INSERT INTO SystemSettings (setting_key, setting_value) VALUES ('primary_currency_code', 'LBP');
INSERT INTO SystemSettings (setting_key, setting_value) VALUES ('secondary_currency_code', 'USD');

-- Note: Pre-defined users and sample menu data should be added via a separate seeding script
-- or manually after tables are created, ensuring passwords are properly hashed by the application.
-- Example (conceptual - hashing needed):
-- INSERT INTO Users (username, hashed_password, full_name, role, is_active) VALUES
-- ('courier1', 'hashed_password_for_courier1', 'Courier One', 'courier', TRUE);
-- ('cashier1', 'hashed_password_for_cashier1', 'Cashier One', 'cashier', TRUE);
-- ('barista1', 'hashed_password_for_barista1', 'Barista One', 'barista', TRUE);
-- ('manager1', 'hashed_password_for_manager1', 'Manager One', 'manager', TRUE);
```
