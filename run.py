"""
Main entry point for the Cafe24 POS Flask application.

This module initializes the Flask application, provides CLI commands for database
operations, and starts the development server.
"""
import logging

from flask import request

from app import create_app, db

# Set up basic logging to console
logging.basicConfig(level=logging.INFO)

app = create_app()


@app.cli.command("create-db")
def create_db_command():
    """Create the database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created.")


@app.cli.command("seed-db")
def seed_db_command():
    """Seed the database with initial data."""
    with app.app_context():
        from app.models import SystemSettings, User, UserRole
        
        # Create default system settings
        settings_data = [
            ('USD_TO_LBP_EXCHANGE_RATE', '90000.0'),
            ('LBP_ROUNDING_FACTOR', '5000'),
            ('CURRENCY_DISPLAY_MODE', 'both'),
            ('DEFAULT_PAYMENT_METHOD', 'cash'),
            ('ENABLE_STOCK_TRACKING', 'true'),
            ('LOW_STOCK_THRESHOLD', '10'),
            ('ENABLE_CUSTOMER_DISPLAY', 'true'),
            ('RECEIPT_FOOTER_TEXT', 'Thank you for visiting Cafe24!'),
        ]
        
        for key, value in settings_data:
            existing = SystemSettings.query.filter_by(setting_key=key).first()
            if not existing:
                setting = SystemSettings(setting_key=key, setting_value=value)
                db.session.add(setting)
        
        # Create default users
        default_users = [
            ('manager', 'password123', 'System Manager', UserRole.manager),
            ('cashier', 'password123', 'Cashier User', UserRole.cashier),
            ('barista', 'password123', 'Barista User', UserRole.barista),
            ('courier', 'password123', 'Courier User', UserRole.courier),
        ]
        
        for username, password, full_name, role in default_users:
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                user = User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    is_active=True
                )
                user.set_password(password)
                db.session.add(user)
        
        try:
            db.session.commit()
            print("Database seeded successfully.")
        except Exception as exc:
            db.session.rollback()
            print(f"Error seeding database: {exc}")


@app.cli.command("migrate-db")
def migrate_db_command():
    """Run database migrations."""
    try:
        from flask_migrate import Migrate, upgrade
        migrate = Migrate(app, db)  # pylint: disable=unused-variable
        with app.app_context():
            upgrade()
            print("Database migrations completed.")
    except ImportError:
        print("Flask-Migrate not installed. Skipping migrations.")
    except Exception as exc:
        print(f"Migration error: {exc}")


@app.before_request
def log_request_info():
    """Log request information for debugging."""
    if request.endpoint and request.endpoint != 'static':
        app.logger.info('Request: %s %s', request.method, request.url)


@app.after_request
def log_response_info(response):
    """Log response information for debugging."""
    if request.endpoint and request.endpoint != 'static':
        app.logger.info('Response: %s', response.status_code)
    return response


if __name__ == '__main__':
    try:
        print("Starting Cafe24 POS server...")
        print("Access the application at: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as exc:
        print(f"Failed to start server: {exc}")
