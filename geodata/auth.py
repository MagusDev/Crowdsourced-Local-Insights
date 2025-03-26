"""
Authentication module for the API.
"""

import secrets
from flask import request

from werkzeug.exceptions import Forbidden
from .models import ApiKey

def require_admin(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("Geodata-Api-Key")
        if not api_key:
            raise Forbidden("API key required")
            
        key_hash = ApiKey.key_hash(api_key.strip())
        db_key = ApiKey.query.filter_by(admin=True).first()
        if db_key and secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden("Invalid API key")
    return wrapper

def require_user_auth(func):
    def wrapper(*args, **kwargs):
        self = args[0]  # Get the resource instance
        user = kwargs.get('user')  # Get the user from kwargs
        
        api_key = request.headers.get("Geodata-Api-Key")
        if not api_key:
            raise Forbidden("API key required")
            
        key_hash = ApiKey.key_hash(api_key.strip())
        db_key = ApiKey.query.filter_by(user_id=user.id).first()
        if db_key and secrets.compare_digest(key_hash, db_key.key):
            return func(*args, **kwargs)
        raise Forbidden("Invalid API key")
    return wrapper