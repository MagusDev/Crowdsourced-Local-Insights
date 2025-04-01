"""
This module define resource for user.
"""

import json
from flask import Response, request
from flask import  url_for
import flask_restful
from sqlalchemy.exc import IntegrityError
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType
from geodata.models import *
from geodata.auth import require_admin, require_user_auth, get_authenticated_user
from geodata.utils import GeodataBuilder
from constants import *
import secrets
from geodata.models import ApiKey

draft7_format_checker = Draft7Validator.FORMAT_CHECKER


class UserCollection(flask_restful.Resource):
    """Resource for handling user collection"""

    def get(self):
        """
        Retrieve a collection of users in Mason format.

        Returns a list of users with limited public information (short form).
        Adds Mason controls for self, user creation, and individual user access.
        """

        body = GeodataBuilder()

        body["@type"] = "users"
        body.add_control("self", url_for("api.usercollection"))
        body.add_control_add_user()
        body["items"] = []
        for user in User.query.all():
            item = user.serialize(short_form=True)
            item["@type"] = "user"
            item.add_control("self", url_for("api.useritem", user=user.username))
            item.add_control("profile", href=USER_PROFILE_URL)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        """
        Register a new user with a unique username and email.
        Validates request body against user schema, hashes the password, 
        creates a default API key, and returns the created user in Mason format.
        """

        if request.content_type != "application/json":
            raise UnsupportedMediaType

        try:
            data = request.get_json()
            validate(data, User.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if User.query.filter_by(
            email=data["email"]).first() or User.query.filter_by(username=data["username"]).first():
            raise Conflict("Username or email already exists.")

        # Create new User
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=User.hash_password(data["password"]),
            first_name=data["first_name"],
            last_name=data.get("last_name", "")
        )
        with db.session.begin():
            db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return GeodataBuilder.create_error_response(409, "Database integrity error.")

        api_key_str = secrets.token_urlsafe(32)
        api_key = ApiKey(
            user_id=new_user.id,
            key=ApiKey.key_hash(api_key_str),
            admin=False,
        )
        with db.session.begin():
            db.session.add(api_key)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return GeodataBuilder.create_error_response(409, "Database integrity error.")

        body = GeodataBuilder(
            id = new_user.id,
            username = new_user.username,
            email = new_user.email,
        )
        body["@type"] = "user"
        body["api_key"] = api_key_str
        body.add_control("self", url_for("api.useritem", user=new_user.username))
        body.add_control_user_collection()
        response = Response(json.dumps(body), 201, mimetype=MASON)
        response.headers["Location"] = url_for("api.useritem", user=new_user.username)
        return response

class UserItem(flask_restful.Resource):
    """Resource for handling individual users"""

    def get(self, user):
        """
        Return a user's data in Mason format.
        If the requester is not authenticated, returns limited data.
        If the requester is the owner or an admin, returns full data.
        """

        # Get current authenticated user (may be None)
        current_user = get_authenticated_user()

        # Check access level
        short = True
        if current_user:
            if current_user.id == user.id or current_user.role == "admin":
                short = False

        # Serialize user data accordingly
        body = GeodataBuilder(user.serialize(short_form=short))
        body["@type"] = "user"
        body.add_namespace("geometa", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.useritem", user=user.username))
        body.add_control("profile", href=USER_PROFILE_URL)
        body.add_control_insights_all()
        body.add_control_insights_by(user)
        body.add_control_feedbacks_by(user)
        if not short:
            body.add_control_delete_user()
            body.add_control_edit_user()
        if current_user.role == "admin":
            body.add_control_user_collection()
        
        return Response(json.dumps(body), 200, mimetype=MASON)


    @require_user_auth
    def put(self, user):
        """
        Update a user's data.
        Only the user themselves or an admin can perform this operation.
        Requires valid JSON and schema-compliant payload.
        """

        current_user = get_authenticated_user()

        # Check permissions
        if not current_user or not current_user.is_owner_or_admin(user.id):
            return GeodataBuilder.create_error_response(
                403,
                "You are not authorized to update this user."
            )
        
        # Validate content type
        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415,
                "Content-Type must be application/json."
            )
        
        # Parse and validate JSON payload
        try:
            data = request.get_json()
            validate(data, User.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(400, f"Invalid input: {str(e)}")
        except Exception:
            return GeodataBuilder.create_error_response(400, "Malformed JSON or request body.")

        # Base fields allowed for all users
        allowed_fields = [
            "username", "email", "phone", "password", "first_name",
            "last_name", "profile_picture", "status"
        ]
        if current_user.is_admin():
            allowed_fields.extend(["role"])  # Only admins can update role

        for field in allowed_fields:
            if field in data:
                if field == "password":
                    user.password = User().hash_password(data["password"])
                elif field == "status":
                    user.set_status(StatusEnum[data["status"].upper()])
                elif field == "role":
                    if current_user.id == user.id and data["role"].upper() != "ADMIN":
                        return GeodataBuilder.create_error_response(
                            400, "You cannot remove your own admin rights."
                        )
                    user.set_role(RoleEnum[data["role"].upper()])
                else:
                    setattr(user, field, data[field])

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return GeodataBuilder.create_error_response(
                409,
                f"Database conflict: {str(e.orig)}"
            )

        # Build Mason-formatted response with updated user data
        body = GeodataBuilder(user.serialize())
        body["@type"] = "user"
        body.add_namespace("geometa", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.useritem", user=user.username))
        body.add_control_edit_user()
        body.add_control_delete_user()

        return Response(json.dumps(body), 200, mimetype=MASON)
    

    @require_user_auth
    def delete(self, user):
        """
        Delete a user by username.
        Allowed only for the account owner or an admin.
        """

        current_user = get_authenticated_user()

        if not current_user or not current_user.is_owner_or_admin(user.id):
            return GeodataBuilder.create_error_response(
                403,
                "You are not authorized to deactivate this user."
            )

        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return GeodataBuilder.create_error_response(
                500,
                "Failed to delete user."
            )

        return Response(status=204)
