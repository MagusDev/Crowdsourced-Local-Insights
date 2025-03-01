from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db/geodata.db"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = test_config["SQLALCHEMY_DATABASE_URI"]  
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from . import models
    from . import api
    from .utils import UserConverter, InsightConverter, FeedbackConverter

    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["insight"] = InsightConverter
    app.url_map.converters["feedback"] = FeedbackConverter
    app.register_blueprint(api.api_bp)

    return app