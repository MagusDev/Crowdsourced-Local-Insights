"""
Authentication module for the API.
    
This module provides basic authentication for the API. It uses the HTTP Basic
Authentication scheme. It also provides a decorator for endpoints that require
admin access.
The outline of the basic HTTPauthentication was implemented with help of 
claude sonnet 3.7 alongside official documentation at 
https://flask-httpauth.readthedocs.io/en/latest/
prompt: "how can i add basic authentication for useraccounts in my flask api?"
"""

from flask_httpauth import HTTPBasicAuth
from flask import g
from werkzeug.exceptions import Forbidden
from .models import User



auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    """Verify username and password"""
    user = User.query.filter_by(username=username).first()
    if user and user.verify_password(password):
        g.user = user
        return True
    return False

def require_admin(func):
    """Decorator for endpoints that require admin access"""
    @auth.login_required
    def wrapper(*args, **kwargs):
        if g.user.role != "ADMIN":
            raise Forbidden("Admin privileges required")
        return func(*args, **kwargs)
    return wrapper

def check_user_access(target_user):
    """
    Check if current user can modify target_user.
    Admin can modify any user, other users can only modify themselves.
    """
    if g.user.role == "ADMIN":
        return True
    return g.user.id == target_user.id
