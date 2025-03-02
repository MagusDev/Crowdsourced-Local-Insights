from flask import Response, request, jsonify
from flask_restful import Resource,  url_for
from sqlalchemy.exc import IntegrityError
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType, Forbidden
from geodata.models import User, db
from geodata.auth import auth

draft7_format_checker = Draft7Validator.FORMAT_CHECKER


class UserCollection(Resource):
    """Resource for handling user collection"""

    def get(self):
        """Get all users"""
        # Help asked from ChatGPT to implement normal json answer to Mason format
        users = User.query.all()
        user_list = [
            {
                "@type": "user",
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "@controls": {
                    "self": {"href": f"/api/users/{user.id}"},
                    "edit": {"href": f"/api/users/{user.id}", "method": "PUT"},
                    "delete": {"href": f"/api/users/{user.id}", "method": "DELETE"},
                }
            }
            for user in users
        ]

        response = {
            "@type": "users",
            "items": user_list,
            "@controls": {
                "self": {"href": "/api/users/"},
                "add": {"href": "/api/users/", "method": "POST"}
            }
        }

        return jsonify(response)

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

        response = jsonify({
            "@type": "user",
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "@controls": {
                "self": {"href": f"/api/users/{new_user.username}"}
            }
        })
        response.headers["Location"] = url_for("api.useritem", user=new_user)
        response.status_code = 201
        return response

class UserItem(Resource):
    """Resource for handling individual users"""

    def get(self, user):
        """Get user by username"""

        response = {
            "@type": "user",
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_date": user.created_date,
            "modified_date": user.modified_date,
            "status": user.status,
            "role": user.role,
            "profile_picture": user.profile_picture,
        }

        return jsonify(response)
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
