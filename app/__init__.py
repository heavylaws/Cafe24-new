"""
Flask application factory for Cafe24 POS system.

This module provides the create_app function that initializes the Flask application
with all necessary extensions, blueprints, and configuration.
"""
import logging
import os

from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name="development"):
    """Working Flask app for Cafe24 POS with routes."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    jwt.init_app(app)

    # Basic CORS
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.menu_routes import menu_bp
    from app.routes.order_routes import order_bp
    from app.routes.report_routes import report_bp
    from app.routes.discount_routes import discount_bp
    from app.routes.ingredient_routes import ingredient_bp
    from app.routes.stock_routes import stock_bp
    from app.routes.category_routes import category_bp
    from app.routes.recipe_routes import recipe_bp
    from app.routes.menu_routes import register_menu_item_options_shim

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(menu_bp, url_prefix='/api/v1/menu')
    app.register_blueprint(order_bp, url_prefix='/api/v1/orders')
    app.register_blueprint(report_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(discount_bp, url_prefix='/api/v1')
    app.register_blueprint(ingredient_bp, url_prefix='/api/v1')
    app.register_blueprint(stock_bp, url_prefix='/api/v1/stock')
    app.register_blueprint(category_bp, url_prefix='/api/v1')
    app.register_blueprint(recipe_bp, url_prefix='/api/v1/menu')

    # System settings endpoint
    from app.routes.menu_routes import get_system_settings, update_system_settings
    app.add_url_rule('/api/v1/system-settings', view_func=get_system_settings, methods=['GET'])
    app.add_url_rule('/api/v1/system-settings', view_func=update_system_settings, methods=['PUT'])

    # Health check
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    # Request logging
    @app.before_request
    def log_request():
        """Log incoming requests."""
        logging.info("%s %s", request.method, request.url)

    register_menu_item_options_shim(app)

    return app
