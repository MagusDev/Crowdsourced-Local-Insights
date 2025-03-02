import enum
import werkzeug.security
from geodata import db

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
    password = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=True)
    created_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    modified_date = db.Column(
        db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
    status = db.Column(db.String, nullable=False, default="ACTIVE")  # Stored as string
    role = db.Column(
        db.String, nullable=False, default="USER")  # Stored as string
    profile_picture = db.Column(
        db.String, nullable=True, default='default_profile_picture_base64_here')

    # Relationship with Insight and Feedback
    insight = db.relationship("Insight", back_populates="user")
    feedback = db.relationship("Feedback", back_populates="user")

    def hash_password(self, password):
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

    @staticmethod
    def get_schema():
        schema = {
            "type" : "object",
            "required" : ["username", "email", "password", "first_name"]
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


class Insight(db.Model):
    """
    Insaight model class.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
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
    modified_date =  db.Column(
        db.DateTime, default = db.func.now(), onupdate = db.func.now(), nullable = False)
    creator = db.Column(db.Integer, db.ForeignKey('user.id',  ondelete="SET NULL"))
    category = db.Column(db.String(64))
    # Restriction - subcategory should be empty when there's no category
    subcategory = db.Column(
        db.String(64),
        db.CheckConstraint(
            'subcategory IS NULL AND category IS NULL OR subcategory IS NOT NULL ',
              name="subcategory_check"))
    external_link = db.Column(db.String(512))
    address = db.Column(db.String(128))
    user = db.relationship('User', back_populates='insight', uselist=False)
    feedback = db.relationship("Feedback", back_populates="insight")


class Feedback(db.Model):
    """
    Feedback model class.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',  ondelete="SET NULL"))
    insight_id = db.Column(db.Integer, db.ForeignKey('insight.id'), nullable=False)
    rating = db.Column(
        db.Integer,
        db.CheckConstraint("rating BETWEEN 1 AND 5 OR rating IS NULL", name="check_rating_range"),
        nullable=True
    )
    comment = db.Column(db.String(512), nullable=True)

    created_date = db.Column(db.DateTime, default = db.func.now(), nullable = False)
    modified_date =  db.Column(
        db.DateTime, default = db.func.now(), onupdate = db.func.now(), nullable = False)

    user = db.relationship("User", back_populates="feedback", uselist=False)
    insight = db.relationship("Insight", back_populates="feedback")

    @staticmethod
    def get_schema():
        schema = {
            "type" : "object",
        }
        props = schema["properties"] = {}
        props["rating"] = {"type": "number"}
        props["comment"] = {"type": "string"}
        return schema
