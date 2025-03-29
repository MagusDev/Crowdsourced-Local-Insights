"""
This module define shared utilities in app
"""
import json
from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from flask import request, Response, url_for
from constants import MASON, ERROR_PROFILE

from geodata.models import User, Insight, Feedback


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

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.
        
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """
    
        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.
        
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )
        
    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """
        
        self.add_control(
            "delete",
            href,
            method="DELETE",
            title=title,
        )

# https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py
# From lnk above, class SensorhubBuilder is used as an example to implement our owm GeodataBuilder
class GeodataBuilder(MasonBuilder):
    """
    A subclass of MasonBuilder that provides some convenience methods for
    adding elements that are specific to the GeoData application. The methods
    in this class are specific to the GeoData application and should not be
    used in other applications.
    """

    def add_control_insights_all(self):
        """
        Add a control to get all insights
        """
        self.add_control(
            "user:get-insights",
            url_for("api.insightcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related insights"
        )

    def add_control_insights_by(self, user):
        """
        Add a control to get all insights
        """
        self.add_control(
            "user:get-insights",
            url_for("api.insightcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related insights"
        )

    def add_control_feedbacks_all(self, user):
        """
        Add a control to get all feedback
        """
        self.add_control(
            "user:get-feedbacks",
            url_for("api.feedbackcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related feedbacks"
        )

    def add_control_feedbacks_by(self, user):
        """
        Add a control to get all feedback
        """
        self.add_control(
            "user:get-feedbacks",
            url_for("api.feedbackcollectionbyuseritem", user=user),
            method="GET",
            title="Get all user related feedbacks"
        )

    def add_control_add_user(self):
        """
        Add a control to add a user
        """
        self.add_control_post(
            "geometa:add-user",
            "Add a new user",
            url_for("api.usercollection"),
            schema=User.get_schema()
        )

    def add_control_add_insight(self, user):
        """
        Add a control to add insight
        """
        self.add_control_post(
            "geometa:add-insight",
            "Add a new insight",
            url_for("api.insightcollection", user=user.username),
            schema=Insight.get_schema()
        )

    def add_control_add_feedback(self, user, insight):
        """
        Add a control to add feedback
        """
        self.add_control_post(
            "geometa:add-feedback",
            "Add a new feedback",
            url_for("api.feedbackcollection", user=user.username, insight=insight.id),
            schema=Feedback.get_schema()
        )

    def add_control_delete_user(self, user):
        """
        Add a control to delete a user
        """
        self.add_control_delete(
            "Delete this user", 
            url_for("api.useritem", user=user.username)
        )

    def add_control_delete_insight(self, user, insight):
        """
        Add a control to delete a insight
        """
        self.add_control_delete(
            "Delete this insight", 
            url_for("api.insightitem", user=user.username, insight=insight.id)
        )

    def add_control_delete_feedback(self, user, insight, feedback):
        """
        Add a control to delete a feedback
        """
        self.add_control_delete(
            "Delete this feedback", 
            url_for("api.feedbackitem",
                    user=user.username,
                    insight=insight.id,
                    feedback=feedback.id
                )
        )

    def add_control_edit_user(self, user):
        """
        Add a control to edit user
        """
        self.add_control_put(
            "Edit this user",
            url_for("api.useritem", user=user.username),
            schema=User.get_schema()
        )
    
    def add_control_edit_insight(self, user, insight):
        """
        Add a control to edit insight
        """
        self.add_control_put(
            "Edit this insight",
            url_for("api.insightitem", user=user.username, insight=insight.id),
            schema=Insight.get_schema()
        )

    def add_control_edit_feedback(self, user, insight, feedback):
        """
        Add a control to edit feedback
        """
        self.add_control_put(
            "Edit this feedback",
            url_for("api.feedbackitem",
                    user=user.username,
                    insight=insight.id,
                    feedback=feedback.id
                ),
            schema=Feedback.get_schema()
        )
    
    @staticmethod
    def create_error_response(status_code, title, message=None):
        """
        Create a MASON-compatible error response with helpful controls.
        """
        builder = GeodataBuilder()
        builder["@type"] = "error"
        builder.add_namespace("error", ERROR_PROFILE)
        builder.add_error(title, message)

        # Add a standard error profile link
        builder.add_control("profile", href=ERROR_PROFILE)

        # Add a 'self' link to the current request path
        builder.add_control("self", href=request.path)

        # Add useful controls based on status code
        if status_code == 401:
            # Suggest login for unauthorized requests
            builder.add_control(
                "auth:login",
                href=url_for("api.usercollection"),  # Could point to login endpoint
                method="POST",
                encoding="json",
                title="Authenticate with API key"
            )

        if status_code == 403:
            # Provide link back to main insights collection
            builder.add_control("home", href=url_for("api.insightcollection"))

        if status_code == 400:
            # Suggest retrying the current action
            builder.add_control("retry", href=request.path, method="POST")
            
        return Response(json.dumps(builder), status=status_code, mimetype=MASON)

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
