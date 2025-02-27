from flask import Flask, Response, request, jsonify
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
        pass

    def put(self, user):
        pass

    def delete(self, user):
        pass