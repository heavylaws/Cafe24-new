import os
import logging

from flask import request
from app import create_app, db, socketio

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
    """Seed the database with initial data for v0.1."""
    with app.app_context():
        from werkzeug.security import generate_password_hash
        from app.models import SystemSettings, User

        # Seed System Settings
        if not SystemSettings.query.filter_by(setting_key="usd_to_lbp_exchange_rate").first():
            db.session.add(SystemSettings(setting_key="usd_to_lbp_exchange_rate", setting_value="90000"))
        if not SystemSettings.query.filter_by(setting_key="primary_currency_code").first():
            db.session.add(SystemSettings(setting_key="primary_currency_code", setting_value="LBP"))
        if not SystemSettings.query.filter_by(setting_key="secondary_currency_code").first():
            db.session.add(SystemSettings(setting_key="secondary_currency_code", setting_value="USD"))

        print("System settings seeded.")

        # Seed Users
        users_to_seed = [
            {"username": "manager1", "password": "password123", "full_name": "Manager One", "role": "manager"},
            {"username": "courier1", "password": "password123", "full_name": "Courier One", "role": "courier"},
            {"username": "barista1", "password": "password123", "full_name": "Barista One", "role": "barista"},
            {"username": "cashier1", "password": "password123", "full_name": "Cashier One", "role": "cashier"},
        ]
        for user_data in users_to_seed:
            if not User.query.filter_by(username=user_data["username"]).first():
                user = User(
                    username=user_data["username"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                )
                user.set_password(user_data["password"])
                db.session.add(user)

        print("Users seeded.")
        print("Menu data seeding placeholder - implement actual data.")

        db.session.commit()
    print("Database seeded with initial v0.1 data.")

@app.cli.command("migrate-db")
def migrate_db_command():
    """Migrate database schema."""
    from flask_migrate import Migrate, upgrade
    migrate = Migrate(app, db)
    upgrade()

if __name__ == "__main__":
    # When running directly (python run.py), it will use the Werkzeug development server.
    # For production, use a WSGI server like Gunicorn

    # Log all requests and errors
    @app.before_request
    def log_request_info():
        """Log incoming request information."""
        logging.info("Request: %s %s", request.method, request.url)

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle unhandled exceptions."""
        logging.exception("Unhandled Exception: %s", e)
        return {"message": "Internal server error"}, 500

    try:
        # Use SocketIO to run the app for WebSocket support
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.exception("Failed to start app: %s", e)
