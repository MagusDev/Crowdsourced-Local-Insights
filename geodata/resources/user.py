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
from geodata.models import User, db
from geodata.auth import auth
from geodata.utils import GeodataBuilder
from geodata.constants import *

draft7_format_checker = Draft7Validator.FORMAT_CHECKER


class UserCollection(flask_restful.Resource):
    """Resource for handling user collection"""

    def get(self):
        """Get all users"""
        body = GeodataBuilder()

        body["@type"] = "users"
        body.add_control("self", url_for("api.usercollection"))
        body.add_control_add_user()
        body["items"] = []
        for user in User.query.all():
            item = GeodataBuilder(
                id = user.id,
                fullname = user.lastname + " " + user.firstname,
                username = user.username,
                email = user.email,
                status = user.status
            )
            item["@type"] = "user"
            item.add_control("self", url_for("api.useritem", user=user))
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        """Create new user"""
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
            password=User().hash_password(data["password"]),
            first_name=data["first_name"],
            last_name=data.get("last_name", "")
        )
        db.session.add(new_user)
        db.session.commit()

        body = GeodataBuilder(
            id = new_user.id,
            username = new_user.username,
            email = new_user.email,
        )
        body["@type"] = "user"
        body.add_control("self", url_for("api.useritem", user=new_user))
        body.add_control("collection", url_for("api.usercollection"))
        return Response(json.dumps(body), 201, mimetype=MASON)

class UserItem(flask_restful.Resource):
    """Resource for handling individual users"""

    def get(self, user):
        """Get user by username"""

        body = GeodataBuilder(
            id = user.id,
            username = user.username,
            email = user.email,
            first_name = user.first_name,
            last_name = user.last_name,
            created_date = user.created_date,
            modified_date = user.modified_date,
            status = user.status,
            role = user.role,
            profile_picture = user.profile_picture
        )
        body["@type"] = "user"
        body.add_control("self", url_for("api.useritem", user=user))
        body.add_control("collection", url_for("api.usercollection"))
        body.add_control_edit_user(user)
        body.add_control_add_insight(user)
        body.add_control_get_insights(user)
        body.add_control_get_feedbacks(user)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @auth.login_required
    def put(self, user):
        """Update user by username"""

        if request.content_type != "application/json":
            raise UnsupportedMediaType
        try:
            data = request.get_json()
            validate(data, User.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e



        user.username = request.json["username"]
        user.email = request.json["email"]
        user.phone = request.json.get("phone", None)
        user.password = User().hash_password(request.json["password"])
        user.first_name = request.json["first_name"]
        user.last_name = request.json["last_name"]
        user.status = request.json["status"]
        user.role = request.json["role"]
        user.profile_picture = request.json.get("profile_picture", None)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return Response(status=409)



        return Response(status=204)
    @auth.login_required
    def delete(self, user):
        """Delete user by username"""

        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
