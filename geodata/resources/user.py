from flask import Flask, Response, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from models import User, db
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
draft7_format_checker = Draft7Validator.FORMAT_CHECKER


class UserCollection(Resource):

    def get(self):
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
        if request.content_type != "application/json":
            raise UnsupportedMediaType

        try:
            data = request.get_json()
            validate(data, User.json_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e
        
        required_fields = ["username", "email", "password", "first_name"]
        if not all(field in data for field in required_fields):
            raise BadRequest("Missing required fields: username, email, password, first_name.")

        if User.query.filter_by(email=data["email"]).first() or User.query.filter_by(username=data["username"]).first():
            raise Conflict("Username or email already exists.")
        
        # Create new User
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=data["password"],  # Salasanan hash pitäisi lisätä
            first_name=data["first_name"],
            last_name=data.get("last_name", "")
        )
        db.session.add(new_user)
        db.session.commit()

        response = {
            "@type": "user",
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "@controls": {
                "self": {"href": f"/api/users/{new_user.id}"}
            }
        }
        return Response(jsonify(response), status=201, mimetype="application/json")

class UserItem(Resource):

    def get(self, user):
        if request.content_type != "application/json":
            raise UnsupportedMediaType
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

    def put(self, user):
        if request.content_type != "application/json":
            raise UnsupportedMediaType
        user_data = request.get_json()
        user.username = user_data.get("username", user.username)
        user.email = user_data.get("email", user.email)
        user.first_name = user_data.get("first_name", user.first_name)
        user.last_name = user_data.get("last_name", user.last_name)
        user.status = user_data.get("status", user.status)  
        user.role = user_data.get("role", user.role)
        user.profile_picture = user_data.get("profile_picture", user.profile_picture)
        db.session.commit()
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

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)