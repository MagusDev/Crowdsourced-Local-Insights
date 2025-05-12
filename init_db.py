"""
This module initializes db for app.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from geodata import db
from run import app

with app.app_context():
    db.create_all()
