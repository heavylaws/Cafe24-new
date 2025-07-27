"""
Flask application factory for the Cafe24 POS system.

This module creates and configures the Flask application with all necessary
extensions, blueprints, and error handlers.
"""
import logging

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config_by_name

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name='development'):
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    
    return app


def register_blueprints(app):
    """
    Register all application blueprints.
    
    Args:
        app (Flask): Flask application instance
    """
    # Import blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.category_routes import category_bp
    from app.routes.discount_routes import discount_bp
    from app.routes.ingredient_routes import ingredient_bp
    from app.routes.menu_routes import menu_bp
    from app.routes.order_routes import order_bp
    from app.routes.recipe_routes import recipe_bp
    from app.routes.report_routes import report_bp
    from app.routes.stock_routes import stock_bp
    from app.routes.unit_routes import unit_bp
    
    # Register API blueprints
    blueprints = [
        (auth_bp, '/api/v1/auth'),
        (menu_bp, '/api/v1/menu'),
        (order_bp, '/api/v1/orders'),
        (report_bp, '/api/v1/reports'),
        (discount_bp, '/api/v1/discounts'),
        (ingredient_bp, '/api/v1/ingredients'),
        (stock_bp, '/api/v1/stock'),
        (category_bp, '/api/v1/categories'),
        (recipe_bp, '/api/v1/recipes'),
        (unit_bp, '/api/v1/units'),
    ]
    
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
    
    # Register additional menu routes
    from app.routes.menu_routes import register_menu_item_options_shim
    register_menu_item_options_shim(app)


def register_error_handlers(app):
    """
    Register global error handlers.
    
    Args:
        app (Flask): Flask application instance
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error('Server Error: %s', error)
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors."""
        return {'error': 'Bad request'}, 400


def configure_logging(app):
    """
    Configure application logging.
    
    Args:
        app (Flask): Flask application instance
    """
    if not app.debug:
        # Configure production logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Cafe24 POS startup')
