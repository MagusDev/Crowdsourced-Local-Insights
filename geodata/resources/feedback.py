from flask import Response, jsonify, request
from flask_restful import Resource,  url_for
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType
from geodata.models import Feedback, db
draft7_format_checker = Draft7Validator.FORMAT_CHECKER

class FeedbackCollectionByUserInsightItem(Resource):

    def get(self, insight, user):
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
            "@controls": {
                "self": {"href": f"/api/users/{user.id}/insights/{insight.id}/feedbacks"},
                "add": {"href": f"/api/users/{user.id}/insights/{insight.id}/feedbacks", "method": "POST"}
            }
        }

        return response


    def post(self, insight, user):
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
        response.headers["Location"] = url_for("api.feedbackitembyuserinsightitem", user=user, insight=insight, feedback=new_feedback)

        return response



class FeedbackCollectionByUserItem(Resource):

    def get(self, user):
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

    def get(self,user,insight, feedback):
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
        pass

    def delete(self,user,insight, feedback):
        pass
