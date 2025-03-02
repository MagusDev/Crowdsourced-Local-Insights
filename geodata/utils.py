from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from flask import url_for

from .models import User, Insight, Feedback


# NOTE: This is copied from sensorhub exercise, check if it could be used
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

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

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


class GeoDataBuilder(MasonBuilder):

    def add_control_delete_user(self, user):
        self.add_control(
            "geodata:delete",
            url_for("api.useritem", user=user),
            method="DELETE",
            title="Delete this user"
        )



class UserConverter(BaseConverter):

    def to_python(self, user):
        db_user = User.query.filter(or_(User.username == user, User.email == user)).first()
        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, db_user):
        return db_user.username


class InsightConverter(BaseConverter):

    def to_python(self, insight_uuid):
        db_insight = Insight.query.filter_by(id = insight_uuid).first()
        if db_insight is None:
            raise NotFound
        return db_insight

    def to_url(self, db_insight):
        return str(db_insight.id)

class FeedbackConverter(BaseConverter):

    def to_python(self, feedback_uuid):
        db_feedback = Feedback.query.filter_by(id = feedback_uuid).first()
        if db_feedback is None:
            raise NotFound
        return db_feedback

    def to_url(self, db_feedback):
        return str(db_feedback.id)
