"""
This module define resource for feedback.
"""
import json
from flask_restful import Resource
from flask import url_for,Response, request
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from geodata.models import Feedback, db
from geodata.utils import GeodataBuilder
from geodata.auth import get_authenticated_user
from constants import *
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
        body.add_control_add_feedback(user, insight)

        if insight:
            feedbacks = Feedback.query.filter_by(insight_id=insight.id).all()
            body.add_control("self", url_for("api.feedbackcollection", user=user.username, insight=insight.id))
            body.add_control("up", url_for("api.insightitem", user=user.username, insight=insight.id))
        else:
            feedbacks = Feedback.query.filter_by(user_id=user.id).all()
            body.add_control("self", url_for("api.feedbackcollection", user=user.username))
            body.add_control("up", url_for("api.useritem", user=user.username))

        body["items"] = []
        for feedback in feedbacks:
            item = GeodataBuilder(feedback.serialize())
            item["@type"] = "feedback"
            if insight:
                item.add_control("self", url_for("api.feedbackitem",
                                                 user=user.username,
                                                 insight=insight.id,
                                                 feedback=feedback.id)
                                )
            else:
                item.add_control("self", url_for("api.feedbackitem",
                                                 user=user.username,
                                                 feedback=feedback.id)
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
                415,
                "Content-Type must be application/json."
            )

        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(400, f"Invalid input: {str(e)}")
        except Exception:
            return GeodataBuilder.create_error_response(400, "Malformed JSON or request body.")

        current_user = get_authenticated_user()

        new_feedback = Feedback(
            insight_id=insight.id,
            rating=data.get("rating"),
            comment=data.get("comment")
        )

        if current_user:
            new_feedback.user_id = current_user.id

        db.session.add(new_feedback)
        db.session.commit()

        response = Response(status=201)
        response.headers["Location"] = url_for(
            "api.feedbackitem", user=user.username, insight=insight.id, feedback=new_feedback.id
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
                403,
                "You are not authorized to update this feedback."
            )
        
        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415,
                "Content-Type must be application/json."
            )
        
        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(400, f"Invalid input: {str(e)}")
        except Exception:
            return GeodataBuilder.create_error_response(400, "Malformed JSON or request body.")

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
                403,
                "You are not authorized to delete this feedback."
            )

        try:
            db.session.delete(feedback)
            db.session.commit()
            cache.delete(request.path)
        except Exception:
            db.session.rollback()
            return GeodataBuilder.create_error_response(
                500,
                "An error occurred while deleting the feedback."
            )

        return Response(status=204)
    

    def prepare_feedback_response(self, user, feedback, current_user, insight=None):
        body = GeodataBuilder()
        if not insight:
            if not current_user or not current_user.is_owner_or_admin(user.id):
                # self refers to insight's feedback
                self_url = url_for(
                    "api.feedbackitem",
                    user=user.username,
                    insight=feedback.insight_id,
                    feedback=feedback.id
                )
                # self refers to insight's feedbackcollection
                collection_url = url_for(
                    "api.feedbackcollection",
                    user=user.username,
                    insight=feedback.insight_id
                )
            else:
                # self refers to user's feedback when owner/admin
                self_url = url_for(
                    "api.feedbackitem",
                    user=user.username,
                    feedback=feedback.id
                )
                # up refers to user's feedbackcollection when owner/admin
                collection_url = url_for(
                    "api.feedbackcollection",
                    user=user.username
                )
                # controls for editing or deleting feedback when owner/admin
                body.add_control_delete_feedback(self_url)
                body.add_control_edit_feedback(self_url)
        else:
            self_url = url_for(
                "api.feedbackitem",
                user=user.username,
                insight=insight.id,
                feedback=feedback.id
            )
            collection_url = url_for(
                "api.feedbackcollection",
                user=user.username,
                insight=insight.id
            )

        body.update(feedback.serialize())
        body["@type"] = "feedback"
        body.add_namespace("geometa", LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("collection", collection_url, title="Collection")
        body.add_control("profile", href=FEEDBACK_PROFILE_URL)
        body.add_control("up", url_for("api.insightitem", insight=feedback.insight_id))
        if feedback.user_id:
            body.add_control("author", url_for("api.useritem", user=feedback.user_id))
        
        return body
