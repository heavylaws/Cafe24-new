"""Authentication and authorization decorators for the Cafe24 POS application.

This module contains decorators for JWT token validation and role-based access control.
"""
import inspect
import logging
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User


def _get_current_user_from_jwt():
    """Extract the User instance from the JWT.
    
    Returns:
        User: The current user or None if not found.
    """
    user_id_str = get_jwt_identity()
    try:
        user_id = int(user_id_str)  # Tokens store integer user IDs
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


def token_required(fn):
    """Decorator that ensures a valid JWT is provided and injects the current user.

    Usage::

        @token_required
        def my_route(current_user):
            ...
    """

    @wraps(fn)
    def decorated_function(*args, **kwargs):
        from flask import request
        if request.method == 'OPTIONS':
            return '', 200

        # This will abort with the appropriate response if token is missing/invalid
        verify_jwt_in_request()
        user = _get_current_user_from_jwt()
        if user is None:
            logging.warning("token_required: Invalid token or user not found.")
            return jsonify({"msg": "Invalid token"}), 401

        # Check if first argument is already a user (from another decorator)
        if args and hasattr(args[0], 'id') and hasattr(args[0], 'username'):
            # First argument is already a user, dont inject another
            return fn(*args, **kwargs)

        # Inject user as first positional arg if the function expects it
        if 'current_user' in inspect.signature(fn).parameters:
            return fn(user, *args, **kwargs)
        # Otherwise, call without injecting to avoid unexpected args
        return fn(*args, **kwargs)

    return decorated_function


def roles_required(*roles):
    """Ensure the current user has at least one of the given roles.

    The decorator is flexible: it accepts either a variable number of
    role strings (``@roles_required('manager', 'cashier')``) *or* a single
    iterable of role strings (``@roles_required(['manager', 'cashier'])``).
    """
    # Flatten roles so we always end up with a list of strings
    allowed_roles = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            allowed_roles.extend(list(r))
        else:
            allowed_roles.append(r)

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            from flask import request
            if request.method == 'OPTIONS':
                return '', 200

            # Get user from args if already injected by token_required
            user = None
            if args and hasattr(args[0], 'id') and hasattr(args[0], 'username'):
                user = args[0]
            else:
                # Ensure a valid JWT and get user
                verify_jwt_in_request()
                user = _get_current_user_from_jwt()
                if user is None:
                    logging.warning("roles_required: Invalid token or user not found.")
                    return jsonify({"msg": "Invalid token"}), 401

            if not getattr(user, 'role', None):
                logging.warning("roles_required: User %s has no role.", user)
                return jsonify({"msg": "Invalid user role"}), 403
            user_role_value = user.role.value if hasattr(user.role, 'value') else user.role
            if user_role_value not in allowed_roles:
                logging.warning("roles_required: User %s with role %s not in allowed roles: %s",
                              user.username, user_role_value, allowed_roles)
                message = f"Access restricted: Requires one of: {', '.join(allowed_roles)}"
                return jsonify({"msg": message}), 403

            # If user was already in args, don't inject again
            if args and hasattr(args[0], 'id') and hasattr(args[0], 'username'):
                return fn(*args, **kwargs)

            # Inject current_user into the wrapped route if requested
            if 'current_user' in inspect.signature(fn).parameters:
                return fn(user, *args, **kwargs)
            return fn(*args, **kwargs)
        return decorator
    return wrapper

