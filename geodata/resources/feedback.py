"""
This module define resource for feedback.
"""
from flask_restful import Resource
from flask import url_for,Response, request
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from geodata.models import Feedback, db
draft7_format_checker = Draft7Validator.FORMAT_CHECKER

class FeedbackCollectionByUserInsightItem(Resource):
    """
    Resource for handling feedback collection by user and insight.
    """

    def get(self, insight, user):
        """get all feedbacks for a user and insight"""

        feedbacks = Feedback.query.filter_by(insight_id=insight.id, user_id = user.id).all()
        feedback_list = [{
            "@type": "feedback",
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "user": feedback.user.username if feedback.user else None,
            "insight": feedback.insight.id,
        } for feedback in feedbacks]

        response = {
            "@type": "feedbacks",
            "items": feedback_list,
        }

        return response


    def post(self, insight, user):
        """create a new feedback for a user and insight"""

        if request.content_type != "application/json":
            raise UnsupportedMediaType

        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        #if Feedback.query.filter_by(insight_id=insight.id, user_id=user.id).first():
        #    raise Conflict("Feedback already exists.")

        new_feedback = Feedback(
            user_id=user.id,
            insight_id=insight.id,
            rating=data["rating"],
            comment=data["comment"],
        )

        db.session.add(new_feedback)
        db.session.commit()

        response = Response(status=201)
        response.headers["Location"] = url_for(
            "api.feedbackitembyuserinsightitem",
                user=user, insight=insight, feedback=new_feedback)

        return response



class FeedbackCollectionByUserItem(Resource):
    """
    Resource for handling feedback collection by user.
    """

    def get(self, user):
        """get all feedbacks for a user"""

        feedbacks = Feedback.query.filter_by(user_id=user.id).all()
        feedback_list = [{
            "@type": "feedback",
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "user": feedback.user.username if feedback.user else None,
            "insight": feedback.insight.id,
        } for feedback in feedbacks]

        response = {
            "@type": "feedbacks",
            "items": feedback_list,
        }

        return response

class FeedbackItemByUserInsightItem(Resource):
    """
    Resource for handling feedback item by user and insight.
    """

    def get(self,user,insight, feedback):
        """
        get a feedback for a user and insight
        itentionally not unused parameter user and insight
        for the conflict with the converter passed parameter
        """

        response = {
            "@type": "feedback",
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "user": feedback.user.username if feedback.user else None,
            "insight": feedback.insight.id,
        }

        return response


    def put(self,user,insight, feedback):
        """
        update a feedback for a user and insight
        itentionally not unused parameter user and insight
        for the conflict with the converter passed parameter
        """

        if request.content_type != "application/json":
            raise UnsupportedMediaType

        try:
            data = request.get_json()
            validate(data, Feedback.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        feedback.rating = data["rating"]
        feedback.comment = data["comment"]

        db.session.commit()

        return Response(status=204)




    def delete(self,user,insight, feedback):
        """
        delete a feedback for a user and insight
        itentionally not unused parameter user and insight
        for the conflict with the converter passed parameter
        """

        db.session.delete(feedback)
        db.session.commit()
        return Response(status=204)
