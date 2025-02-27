from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db/test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from . import models
    from . import api
    from .utils import UserConverter, InsightConverter

    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["insight"] = InsightConverter
    app.register_blueprint(api.api_bp)

    return app