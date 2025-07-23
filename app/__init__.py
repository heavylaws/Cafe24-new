from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import MetaData

load_dotenv()

# Define a naming convention for database constraints
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'a-super-secret-jwt-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pos_system_v01.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT configuration for flask_jwt_extended
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Logging configuration
    logging.basicConfig(level=logging.INFO)

    # --- File logging setup ---
    logs_dir = os.path.join(os.path.abspath(os.getcwd()), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    file_handler = RotatingFileHandler(os.path.join(logs_dir, 'backend.log'), maxBytes=1_048_576, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    # Avoid duplicate handlers if create_app is called multiple times (e.g., in tests)
    if not any(isinstance(h, RotatingFileHandler) for h in logging.getLogger().handlers):
        logging.getLogger().addHandler(file_handler)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    jwt.init_app(app)
    # Enable CORS for all API routes and allow credentials
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
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(menu_bp, url_prefix='/api/v1/menu')
    app.register_blueprint(order_bp, url_prefix='/api/v1/orders')
    app.register_blueprint(report_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(discount_bp, url_prefix='/api/v1')
    app.register_blueprint(ingredient_bp, url_prefix='/api/v1')
    app.register_blueprint(stock_bp, url_prefix='/api/v1/stock')
    app.register_blueprint(category_bp, url_prefix='/api/v1')
    app.register_blueprint(recipe_bp, url_prefix='/api/v1/recipes')

    # Expose system settings at /api/v1/system-settings (frontend expects this)
    from app.routes.menu_routes import get_system_settings, update_system_settings  # noqa: E402
    app.add_url_rule('/api/v1/system-settings', view_func=get_system_settings, methods=['GET'])
    app.add_url_rule('/api/v1/system-settings', view_func=update_system_settings, methods=['PUT'])

    # --- Request & error logging ---
    from flask import request, jsonify  # imported here to avoid circular deps

    @app.after_request
    def log_request(response):
        logging.getLogger('request').info('%s %s %s -> %s', request.remote_addr, request.method, request.full_path, response.status)
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logging.getLogger('error').exception('Unhandled exception: %s', err)
        return jsonify({'message': 'Internal server error'}), 500

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app

