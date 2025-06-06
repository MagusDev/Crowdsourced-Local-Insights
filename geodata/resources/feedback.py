"""
This module define resource for feedback.
"""

import json
from flask_restful import Resource
from flask import url_for, Response, request
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from geodata.models import Feedback, db
from geodata.utils import GeodataBuilder
from geodata.auth import get_authenticated_user
from geodata.constants import *

draft7_format_checker = Draft7Validator.FORMAT_CHECKER
from geodata import cache


class FeedbackCollection(Resource):
    """
    Resource for handling feedback collection by user and insight.
    """

    def get(self, user, insight=None):
        """
        Return feedback(s) submitted by a user if only user is provided.
        If insight is provided, filter feedback by insight.
        """
        body = GeodataBuilder()
        body["@type"] = "feedbacks"
        body.add_namespace("geometa", LINK_RELATIONS_URL)

        if insight:
            body.add_control_add_feedback(user, insight)

        if insight:
            feedbacks = Feedback.query.filter_by(insight_id=insight.id).all()
            body.add_control(
                "self", url_for("api.feedbacks_by_insight", user=user, insight=insight)
            )
            body.add_control("up", url_for("api.insight", user=user, insight=insight))
        else:
            feedbacks = Feedback.query.filter_by(user_id=user.id).all()
            body.add_control("self", url_for("api.feedbacks_by_user", user=user))
            body.add_control("up", url_for("api.user", user=user))

        body["items"] = []
        for feedback in feedbacks:
            item = GeodataBuilder(feedback.serialize())
            item["@type"] = "feedback"
            if insight:
                item.add_control(
                    "self",
                    url_for(
                        "api.feedback_by_insight",
                        user=user,
                        insight=insight,
                        feedback=feedback,
                    ),
                )
            else:
                item.add_control(
                    "self",
                    url_for("api.feedback_by_user", user=user, feedback=feedback),
                )
            item.add_control("profile", href=FEEDBACK_PROFILE_URL)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, user, insight):
        """
        Create a new feedback for an insight and if logged in it will be added under user also.
        """

        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415, "Content-Type must be application/json."
            )

        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(400, f"Invalid input: {str(e)}")

        current_user = get_authenticated_user()

        new_feedback = Feedback(
            insight_id=insight.id,
            rating=data.get("rating"),
            comment=data.get("comment"),
        )

        if current_user:
            new_feedback.user_id = current_user.id

        db.session.add(new_feedback)
        db.session.commit()

        response = Response(status=201)
        response.headers["Location"] = url_for(
            "api.feedback_by_insight", user=user, insight=insight, feedback=new_feedback
        )
        return response


class FeedbackItem(Resource):
    """
    Resource for handling feedback item by user and insight.
    """

    @cache.cached()
    def get(self, user, feedback, insight=None):
        """
        Return a single feedback item in Mason format.

        - If 'insight' is provided, the feedback is considered public and accessible by anyone.
        - If 'insight' is not provided, access is allowed only for the feedback's owner or an admin.
        - If access is denied and 'insight' is not provided, the request is internally redirected
        using feedback.insight_id to construct the public insight-based route.
        - Adds Mason hypermedia controls including 'self', 'up', 'profile', and optionally 'author'.
        """

        current_user = get_authenticated_user()

        body = self.prepare_feedback_response(user, feedback, current_user, insight)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, user, feedback, insight=None):
        """
        Update an existing feedback.
        Allowed only for the feedback's owner or an admin.
        """

        current_user = get_authenticated_user()

        if not current_user or not current_user.is_owner_or_admin(feedback.user_id):
            return GeodataBuilder.create_error_response(
                403, "You are not authorized to update this feedback."
            )

        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415, "Content-Type must be application/json."
            )

        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(400, f"Invalid input: {str(e)}")

        feedback.rating = data.get("rating")
        feedback.comment = data.get("comment")

        db.session.commit()
        cache.delete(request.path)

        # Build Mason response
        body = self.prepare_feedback_response(user, feedback, current_user, insight)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def delete(self, user, feedback, insight=None):
        """
        Delete a feedback.
        Allowed only for the feedback's owner or an admin.
        """

        current_user = get_authenticated_user()

        if not current_user or not current_user.is_owner_or_admin(feedback.user_id):
            return GeodataBuilder.create_error_response(
                403, "You are not authorized to delete this feedback."
            )

        # remoced the try except block for error 500
        db.session.delete(feedback)
        db.session.commit()
        cache.delete(request.path)

        db.session.rollback()

        return Response(status=204)

    def prepare_feedback_response(self, user, feedback, current_user, insight=None):
        body = GeodataBuilder()
        if not insight:
            if not current_user or not current_user.is_owner_or_admin(user.id):
                # self refers to insight's feedback
                self_url = url_for(
                    "api.feedback_by_insight",
                    user=user,
                    insight=feedback,
                    feedback=feedback,
                )
                # self refers to insight's feedbackcollection
                collection_url = url_for(
                    "api.feedbacks_by_insight", user=user, insight=feedback.insight
                )
            else:
                # self refers to user's feedback when owner/admin
                self_url = url_for("api.feedback_by_user", user=user, feedback=feedback)
                # up refers to user's feedbackcollection when owner/admin
                collection_url = url_for("api.feedbacks_by_user", user=user)
                # controls for editing or deleting feedback when owner/admin
                body.add_control_delete_feedback(self_url)
                body.add_control_edit_feedback(self_url)
        else:
            self_url = url_for(
                "api.feedback_by_insight", user=user, insight=insight, feedback=feedback
            )
            collection_url = url_for(
                "api.feedbacks_by_insight", user=user, insight=insight
            )

        body.update(feedback.serialize())
        body["@type"] = "feedback"
        body.add_namespace("geometa", LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("collection", collection_url, title="Collection")
        body.add_control("profile", href=FEEDBACK_PROFILE_URL)
        body.add_control("up", url_for("api.insight", insight=feedback.insight))
        if feedback.user:
            body.add_control("author", url_for("api.user", user=feedback.user))

        return body
