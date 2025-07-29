"""Authentication routes for the Cafe24 POS system."""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.models import User, db
from app.schemas import UserSchema

auth_bp = Blueprint("auth_bp", __name__)

user_schema = UserSchema()


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return access token."""
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "Username and password required"}), 400

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"message": "User account is inactive"}), 403

        # The user's ID is now the identity (convert to string for JWT)
        access_token = create_access_token(identity=str(user.id))

        # We still send user details to the frontend for UI setup
        return (
            jsonify(
                access_token=access_token,
                user={"role": user.role.value, "username": user.username},
            ),
            200,
        )

    return jsonify({"message": "Invalid credentials"}), 401