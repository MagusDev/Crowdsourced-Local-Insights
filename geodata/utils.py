from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from flask import url_for

from models import User, Insight, Feedback


# NOTE: This class called MasonBuilder is copied from sensorhub example,
# https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py
# Original implementation modified:
# - to check allowed control properties
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    ALLOWED_PROPERTIES = {
        "href", "isHrefTemplate", "title", "description", "method", "encoding",
        "schema", "schemaUrl", "template", "accept", "output", "files", "alt"
    }

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        # Initialize the control dictionary
        control = {"href": href}
        
        # Validate and add additional properties
        for key, value in kwargs.items():
            if key in self.ALLOWED_PROPERTIES:
                control[key] = value
            else:
                raise ValueError(f"Invalid control property: {key}")
        
        self["@controls"][ctrl_name] = control

# https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py
# From lnk above, class SensorhubBuilder is used as an example to implement our owm GeodataBuilder
class GeodataBuilder(MasonBuilder):
    """
    A subclass of MasonBuilder that provides some convenience methods for
    adding elements that are specific to the GeoData application. The methods
    in this class are specific to the GeoData application and should not be
    used in other applications.
    """

    def add_control_delete_user(self, user):
        self.add_control(
            "user:delete-user",
            url_for("api.useritem", user=user),
            method="DELETE",
            title="Delete this user"
        )

    def add_control_add_user(self):
        self.add_control(
            "user:add-user",
            url_for("api.usercollection"),
            method="POST",
            encoding="json",
            title="Add a new user",
            schema=User.get_schema()
        )

    def add_control_edit_user(self, user):
        self.add_control(
            "user:edit",
            url_for("api.useritem", user=user),
            method="PUT",
            encoding="json",
            title="Edit this user",
            schema=User.get_schema()
        )

    def add_control_add_insight(self, user):
        self.add_control(
            "user:add-insight",
            url_for("api.insightcollectionbyuseritem", user=user),
            method="POST",
            encoding="json",
            title="Add a new insight",
            schema=Insight.get_schema()
        )

    def add_control_get_insights(self, user):
        self.add_control(
            "user:get-insights",
            url_for("api.insightcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related insights"
        )

    def add_control_get_feedbacks(self, user):
        self.add_control(
            "user:get-feedbacks",
            url_for("api.feedbackcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related feedbacks"
        )

class UserConverter(BaseConverter):
    """
    A URL converter for the User model. This converter is used to convert
    between the User model and the username or email that identifies the user
    in the URL. The converter is used in the URL rules in the application
    configuration.
    """

    def to_python(self, value):
        db_user = User.query.filter(or_(User.username == value, User.email == value)).first()
        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, value):
        return value.username


class InsightConverter(BaseConverter):
    """
    A URL converter for the Insight model. This converter is used to convert
    between the Insight model and the UUID that identifies the insight in the
    URL. The converter is used in the URL rules in the application
    configuration
    """

    def to_python(self, value):
        db_insight = Insight.query.filter_by(id = value).first()
        if db_insight is None:
            raise NotFound
        return db_insight

    def to_url(self, value):
        return str(value.id)

class FeedbackConverter(BaseConverter):
    """
    A URL converter for the Feedback model. This converter is used to convert
    between the Feedback model and the UUID that identifies the feedback in the
    URL. The converter is used in the URL rules in the application
    configuration
    """

    def to_python(self, value):
        db_feedback = Feedback.query.filter_by(id = value).first()
        if db_feedback is None:
            raise NotFound
        return db_feedback

    def to_url(self, value):
        return str(value.id)
