"""
This module init app and sets up the db.
"""
import os
import yaml
from flasgger import Swagger
from flask import Flask, send_from_directory
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
cache = Cache()

def create_app(test_config=None):
    """
    Create and config app
    """
    app = Flask(__name__, static_folder="static")
    if test_config is None:
        filepath = os.path.abspath(os.getcwd()) + "/db/geodata.db"
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + filepath

        app.config["SWAGGER"] = {
            "title": "Crowdsourced local insights API",
            "openapi": "3.0.0",
            "uiversion": 3,
            "doc_dir": "./geodata/doc"
        }
        Swagger(app, template_file="doc/swagger_base.yml")
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = test_config["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CACHE_TYPE"] = "FileSystemCache"
    app.config["CACHE_DIR"] = os.path.join(app.instance_path, "cache")
    db.init_app(app)
    cache.init_app(app)


    from .utils import UserConverter, InsightConverter, FeedbackConverter
    from geodata.api_init import api_bp
    from . import api
    from . import models

    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["insight"] = InsightConverter
    app.url_map.converters["feedback"] = FeedbackConverter
    app.register_blueprint(api_bp)

    app.cli.add_command(models.create_admin)
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.populate_db_command)

    @app.route("/profiles/<resource>/")
    def send_profile_html(resource):
        return send_from_directory(app.static_folder, "{}.html".format(resource))
    
    @app.route("/geodata/link-relations/")
    def send_link_relations_html():
        return send_from_directory(app.static_folder, "links-relations.html")

    return app
