import enum
import hashlib
import os
import uuid
from datetime import datetime, timezone
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.exceptions import BadRequest
from sqlalchemy.engine import Engine
from sqlalchemy import event

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Go one step back
DB_PATH = os.path.join(BASE_DIR, "db/test.db")  # Store DB inside the "db" folder

# Ensure the "db" directory exists
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

# Initialize Flask and SQLAlchemy
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Enum classes for status and role (ChatGPT used for implementing this ENUM functionality)
class StatusEnum(enum.Enum):
    active = "active"
    inactive = "inactive"
    banned = "banned"

class RoleEnum(enum.Enum):
    user = "user"
    admin = "admin"
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    phone = db.Column(db.Integer, unique=True, nullable=True)
    password = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    modified_date = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
    status = db.Column(db.String, nullable=False, default="active")  # Stored as string
    role = db.Column(db.String, nullable=False, default="user")  # Stored as string
    profile_picture = db.Column(db.String, nullable=True, default='default_profile_picture_base64_here')

    # Relationship with Insight and Feedback
    insight = db.relationship("Insight", back_populates="user", uselist=False)
    feedback = db.relationship("Feedback", back_populates="user", uselist=False)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    @property
    def status_enum(self):
        return StatusEnum[self.status]

    @property
    def role_enum(self):
        return RoleEnum[self.role]

    # Set status and role using Enum
    def set_status(self, status_enum):
        if isinstance(status_enum, StatusEnum):
            self.status = status_enum.name

    def set_role(self, role_enum):
        if isinstance(role_enum, RoleEnum):
            self.role = role_enum.name


class Insight(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024) )
    longitude = db.Column(
        db.Float, 
        db.CheckConstraint('longitude>=-180 AND longitude <= 180', name = 'longitude_range_check'),
        nullable=False)
    latitude = db.Column(
        db.Float,
        db.CheckConstraint('latitude>=-90 AND latitude <= 90', name = 'latitude_range_check'),
        nullable = False)
    image = db.Column(db.String(128))
    created_date = db.Column(db.DateTime, default = db.func.now(), nullable = False)
    modified_date =  db.Column(db.DateTime, default = db.func.now(), onupdate = db.func.now(), nullable = False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable = False)
    category = db.Column(db.String(64))
    # Restriction - subcategory should be empty when there's no category
    subcategory = db.Column(
        db.String(64),
        db.CheckConstraint('subcategory IS NULL AND category IS NULL OR subcategory IS NOT NULL ', name="subcategory_check"))
    external_link = db.Column(db.String(512))
    address = db.Column(db.String(128))
    user = db.relationship('User', back_populates='insight')
    feedback = db.relationship("Feedback", back_populates="insight", uselist=False)


class Feedback(db.Model):   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    insight_id = db.Column(db.Integer, db.ForeignKey('insight.id'), nullable=False)
    rating = db.Column(
        db.Integer,
        db.CheckConstraint("rating BETWEEN 1 AND 5 OR rating IS NULL", name="check_rating_range"),
        nullable=True
    )
    comment = db.Column(db.String(512), nullable=True)
 
    created_date = db.Column(
        db.DateTime(),
        default= db.func.now(),
        nullable=False
    )
    
    modified_date = db.Column(
        db.DateTime(),
        default=lambda: db.func.now(),
        onupdate=lambda: db.func.now(),
        nullable=False
    )
    
    user = db.relationship("User", back_populates="feedback")
    insight = db.relationship("Insight", back_populates="feedback")

# Set up database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
