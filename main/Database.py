from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from werkzeug.exceptions import BadRequest
from sqlalchemy.engine import Engine
from sqlalchemy import event
import enum
import hashlib

# Initialize Flask and SQLAlchemy
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"  # Replace with your DB URI
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
    __tablename__ = 'user'

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

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    insight_id = db.Column(db.Integer, db.ForeignKey('insight.id'), nullable=False)
    rating = db.Column(
        db.Integer,
        db.CheckConstraint("rating BETWEEN 1 AND 5 OR rating IS NULL", name="check_rating_range"),
        nullable=True
    )
    comment = db.Column(db.String(512), nullable=True)

    #used chatGPT to generate DateTime objects for created_date and modified_date
    # prompt: "The method "utcnow" in class "datetime" is deprecated Use timezone-aware 
    # objects to represent datetimes in UTC; e.g. by calling .now(datetime.timezone.utc)" 
    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    modified_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    user = db.relationship("User", back_populates="feedback")
    insight = db.relationship("Insight", back_populates="feedback")

    def __repr__(self):
        return (f"<Feedback(id={self.id}, user_id={self.user_id}, insight_id={self.insight_id}, "
                f"rating={self.rating}, created_date={self.created_date}, modified_date={self.modified_date})>")

# Set up database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
