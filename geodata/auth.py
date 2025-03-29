"""
Authentication module for the API.
"""

import secrets
from flask import request
from werkzeug.exceptions import Forbidden
from .models import ApiKey


def require_admin(func):
    """
    Decorator to require an admin API key.
    """
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise Forbidden("Missing or invalid Authorization header")
        token = auth_header.split(" ", 1)[1]
        if not token:
            raise Forbidden("API key required")

        key_hash = ApiKey.key_hash(token.strip())
        db_key = ApiKey.query.filter_by(admin=True).first()
        if db_key and secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden("Invalid API key")
    return wrapper


def require_user_auth(func):
    """
    Decorator to require a user API key.
    Mainly used for user specific endpoints put and delete methods.
    """
    def wrapper(*args, **kwargs):
        user = kwargs.get('user')  # Get the user from kwargs

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise Forbidden("Missing or invalid Authorization header")
        token = auth_header.split(" ", 1)[1]
        if not token:
            raise Forbidden("API key required")

        key_hash = ApiKey.key_hash(token.strip())
        db_key = ApiKey.query.filter_by(user_id=user.id).first()
        if db_key and secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden("Invalid API key")
    return wrapper
