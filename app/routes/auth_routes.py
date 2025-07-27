"""
Authentication routes for the Cafe24 POS system.

This module handles user authentication including login and token management.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import SQLAlchemyError

from app.models import db, User
from app.schemas import UserSchema

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return an access token.
    
    Expected JSON payload:
    {
        "username": "user123",
        "password": "password123"
    }
    
    Returns:
        dict: Contains access_token and user information on success
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'message': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Account is deactivated'}), 401
        
        if not user.check_password(password):
            return jsonify({'message': 'Invalid username or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        # Serialize user data
        user_schema = UserSchema()
        user_data = user_schema.dump(user)
        
        return jsonify({
            'access_token': access_token,
            'user': user_data,
            'message': 'Login successful'
        }), 200
        
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({'message': 'Database error occurred'}), 500
    except Exception as exc:
        return jsonify({'message': 'An unexpected error occurred'}), 500


@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """
    Health check endpoint for authentication service.
    
    Returns:
        dict: Service health status
    """
    return jsonify({
        'service': 'auth',
        'status': 'healthy',
        'version': '1.0.0'
    }), 200
