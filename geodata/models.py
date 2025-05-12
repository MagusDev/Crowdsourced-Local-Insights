"""
This module define app models.
"""

import enum
import hashlib
import secrets
import click
from flask.cli import with_appcontext
from flask import url_for
import werkzeug.security
from geodata import db
from PIL import Image
import io
import base64
import geodata.constants


# Enum classes for status and role (ChatGPT used for implementing this ENUM functionality)
class StatusEnum(enum.Enum):
    """
    Enum class for user status.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BANNED = "BANNED"


class RoleEnum(enum.Enum):
    """
    Enum class for user role.
    """

    USER = "USER"
    ADMIN = "ADMIN"


class User(db.Model):
    """
    User model class.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    phone = db.Column(db.Integer, unique=True, nullable=True)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    modified_date = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )
    status = db.Column(db.String, nullable=False, default="ACTIVE")  # Stored as string
    role = db.Column(db.String, nullable=False, default="USER")  # Stored as string
    profile_picture = db.Column(db.String, nullable=True)
    profile_picture_thumb = db.Column(db.String, nullable=True)

    # Relationship with Insight and Feedback
    insight = db.relationship("Insight", back_populates="user")
    feedback = db.relationship("Feedback", back_populates="user")

    api_key = db.relationship("ApiKey", back_populates="user", uselist=False)

    def serialize(self, short_form=False):
        data = {
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "status": self.status,
            "role": self.role,
            "profile_picture_thumb": self.profile_picture_thumb,
        }

        if short_form:
            return data

        # Full serialization
        data.update(
            {
                "email": self.email,
                "phone": self.phone,
                "created_date": (
                    self.created_date.isoformat() if self.created_date else None
                ),
                "modified_date": (
                    self.modified_date.isoformat() if self.modified_date else None
                ),
                "profile_picture": self.profile_picture,
            }
        )

        return data

    @staticmethod
    def hash_password(password):
        """
        Hash the password using werkzeug.security.
        """

        return werkzeug.security.generate_password_hash(password)

    def verify_password(self, password):
        """
        Verify the password using werkzeug.security.
        """

        return werkzeug.security.check_password_hash(self.password, password)

    @property
    def status_enum(self):
        """
        Return the status as an Enum.
        """

        return StatusEnum[self.status]

    @property
    def role_enum(self):
        """
        Return the role as an Enum.
        """

        return RoleEnum[self.role]

    def set_status(self, status_enum):
        """
        Set the status of the user.
        """

        if isinstance(status_enum, StatusEnum):
            self.status = status_enum.name

    def set_role(self, role_enum):
        """
        Set the role of the user.
        """

        if isinstance(role_enum, RoleEnum):
            self.role = role_enum.name

    def is_admin(self):
        return self.role_enum == RoleEnum.ADMIN

    def is_owner_or_admin(self, other_user_id):
        return self.id == other_user_id or self.is_admin()

    @staticmethod
    def get_schema():
        """
        Return the schema for user
        """
        schema = {
            "type": "object",
            "required": ["username", "email", "password", "first_name"],
        }
        props = schema["properties"] = {}
        props["username"] = {"type": "string"}
        props["email"] = {"type": "string"}
        props["phone"] = {"type": "number"}
        props["password"] = {"type": "string"}
        props["first_name"] = {"type": "string"}
        props["last_name"] = {"type": "string"}
        props["status"] = {"type": "string", "enum": ["ACTIVE", "INACTIVE", "BANNED"]}
        props["role"] = {"type": "string", "enum": ["USER", "ADMIN"]}
        props["profile_picture"] = {"type": "string"}
        return schema

    @staticmethod
    def generate_thumbnail(image_data_base64, size=(64, 64)):
        image_data = base64.b64decode(image_data_base64)
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail(size)

        buffer = io.BytesIO()
        image.save(buffer, format="WEBP")  # tai PNG
        thumb_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return thumb_b64


class Insight(db.Model):
    """
    Insight model class.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024))
    longitude = db.Column(
        db.Float,
        db.CheckConstraint(
            "longitude>=-180 AND longitude <= 180", name="longitude_range_check"
        ),
        nullable=False,
    )
    latitude = db.Column(
        db.Float,
        db.CheckConstraint(
            "latitude>=-90 AND latitude <= 90", name="latitude_range_check"
        ),
        nullable=False,
    )
    image = db.Column(db.String(128))
    created_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    modified_date = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )
    creator = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    category = db.Column(db.String(64))
    # Restriction - subcategory should be empty when there's no category
    subcategory = db.Column(
        db.String(64),
        db.CheckConstraint(
            "subcategory IS NULL AND category IS NULL OR subcategory IS NOT NULL ",
            name="subcategory_check",
        ),
    )
    external_link = db.Column(db.String(512))
    address = db.Column(db.String(128))
    user = db.relationship("User", back_populates="insight", uselist=False)
    feedback = db.relationship("Feedback", back_populates="insight")

    def serialize(self, short_form=False):
        # Calculates average of ratings
        ratings = [fb.rating for fb in self.feedback if fb.rating is not None]
        average_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        data = {
            "id": self.id,
            "title": self.title,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "category": self.category,
            "created_date": self.created_date.isoformat(),
            "user": self.user.username if self.user else None,
        }

        if not short_form:
            data.update(
                {
                    "description": self.description,
                    "subcategory": self.subcategory,
                    "image": self.image,
                    "modified_date": (
                        self.modified_date.isoformat() if self.modified_date else None
                    ),
                    "external_link": self.external_link,
                    "address": self.address,
                    "average_rating": average_rating,
                }
            )

        return data

    @staticmethod
    def get_schema():
        """
        Return the schema for insight
        """
        schema = {"type": "object", "required": ["title", "longitude", "latitude"]}
        props = schema["properties"] = {}
        props["title"] = {"type": "string"}
        props["description"] = {"type": "string"}
        props["longitude"] = {"type": "number"}
        props["latitude"] = {"type": "number"}
        props["image"] = {"type": "string"}
        props["address"] = {"type": "string"}
        props["category"] = {"type": "string"}
        props["subcategory"] = {"type": "string"}
        props["external_link"] = {"type": "string"}
        return schema


class Feedback(db.Model):
    """
    Feedback model class.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    insight_id = db.Column(db.Integer, db.ForeignKey("insight.id", ondelete="CASCADE"))
    rating = db.Column(
        db.Integer,
        db.CheckConstraint(
            "rating BETWEEN 1 AND 5 OR rating IS NULL", name="check_rating_range"
        ),
        nullable=True,
    )
    comment = db.Column(db.String(512), nullable=True)

    created_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    modified_date = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False
    )

    user = db.relationship("User", back_populates="feedback", uselist=False)
    insight = db.relationship("Insight", back_populates="feedback")

    def serialize(self):
        return {
            "@type": "feedback",
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "user": self.user.username if self.user else None,
            "insight": self.insight.id if self.insight else None,
            "created_date": (
                self.created_date.isoformat() if self.created_date else None
            ),
            "modified_date": (
                self.modified_date.isoformat() if self.modified_date else None
            ),
        }

    @staticmethod
    def get_schema():
        """
        Return the schema for the feedback
        """
        schema = {
            "type": "object",
        }
        props = schema["properties"] = {}
        props["rating"] = {"type": "number"}
        props["comment"] = {"type": "string"}
        return schema


class ApiKey(db.Model):

    key = db.Column(db.String(32), nullable=False, unique=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    admin = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="api_key", uselist=False)

    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    click.echo("Initializing the database...")
    # db.drop_all()
    db.create_all()
    click.echo("Database initialized successfully!")


@click.command("populate-db")
@with_appcontext
def populate_db_command():
    """Populate database with sample data."""
    # Create sample users
    admin = User(
        username="admin_test",
        email="admin@example.com",
        password=User.hash_password("adminpass"),
        first_name="Admin",
        last_name="User",
        phone=1234567890,
        status="ACTIVE",
    )
    admin.set_role(RoleEnum.ADMIN)

    user = User(
        username="user_test",
        email="user@example.com",
        password=User.hash_password("userpass"),
        first_name="Regular",
        last_name="User",
        phone=9876543210,
        status="ACTIVE",
    )
    user.set_role(RoleEnum.USER)

    db.session.add_all([admin, user])
    db.session.flush()

    # Create sample insights
    insight1 = Insight(
        title="Coffee Shop",
        description="Great local coffee shop with free WiFi",
        longitude=25.4667,
        latitude=65.0167,
        category="Food & Drink",
        subcategory="Cafe",
        address="123 Main St",
        creator=user.id,
    )

    insight2 = Insight(
        title="City Park",
        description="Beautiful park with walking trails",
        longitude=25.4700,
        latitude=65.0200,
        category="Recreation",
        subcategory="Parks",
        address="456 Park Ave",
        creator=admin.id,
    )

    db.session.add_all([insight1, insight2])
    db.session.flush()

    # Create sample feedback
    feedback = Feedback(
        user_id=user.id,
        insight_id=insight2.id,
        rating=5,
        comment="This park is amazing! Perfect for picnics.",
    )

    db.session.add(feedback)
    db.session.commit()

    # Create API key for admin
    api_key_str = secrets.token_urlsafe(32)
    api_key = ApiKey(
        user_id=admin.id,
        key=ApiKey.key_hash(api_key_str),
        admin=True,
    )
    db.session.add(api_key)
    db.session.commit()

    click.echo("Database populated with sample data!")
    click.echo(f"Admin user created with username: admin_test, password: adminpass")
    click.echo(f"Regular user created with username: user_test, password: userpass")
    click.echo(f"Admin API key: {api_key_str}")


@click.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def create_admin(username, email, password):
    """Create an admin user from command line"""
    user = User(
        username=username,
        email=email,
        password=User.hash_password(password),
        first_name="Admin",
        last_name="User",
    )
    user.set_role(RoleEnum.ADMIN)
    db.session.add(user)
    db.session.flush()

    # Create admin API key
    api_key_str = secrets.token_urlsafe(32)
    api_key = ApiKey(
        user_id=user.id,
        key=ApiKey.key_hash(api_key_str),
        admin=True,
    )
    db.session.add(api_key)
    db.session.commit()
    print(f"Admin created. API key: {api_key_str}")
    return api_key_str
