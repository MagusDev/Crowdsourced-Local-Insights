"""
This module defines insight resource.
"""
from datetime import datetime
from flask import request
from flask_restful import Resource
from werkzeug.exceptions import UnsupportedMediaType
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from geodata import db
from geodata.models import Insight


class InsightItem(Resource):
    """
      Resource for single insight with all the details
    """
    def get(self, insight):
        """
          Get a single insight by id
        """
        insight = Insight.query.filter_by(id=insight.id).first()
        if insight is None:
            return "No matching insight", 404
        response = {
            "id": insight.id,
            "title": insight.title,
            "description": insight.description,
            "longitude": insight.longitude,
            "latitude": insight.latitude,
            "image": insight.image,
            "created_date": insight.created_date.isoformat(),
            "modified_date": insight.modified_date.isoformat(),
            "creator": insight.creator,
            "category": insight.category,
            "subcategory": insight.subcategory,
            "external_link": insight.external_link,
            "address": insight.address
        }
        return response, 200

    def put(self, insight):
        """
          Update a single insight
        """
        if request.content_type != "application/json":
            raise UnsupportedMediaType

        payload = request.get_json()
        updated_insight = Insight.query.filter_by(id=insight.id).first()
        updated_insight.title = payload["title"]
        updated_insight.description = payload["description"]
        updated_insight.longitude = payload["longitude"]
        updated_insight.latitude = payload["latitude"]
        updated_insight.image = payload["image"]
        updated_insight.address = payload["address"]
        updated_insight.category = payload["category"]
        updated_insight.subcategory = payload["subcategory"]
        updated_insight.external_link = payload["external_link"]
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 409
        return 204

    def delete(self, insight):
        """
          delete a single insight
        """
        insight = Insight.query.filter_by(id=insight.id).first()
        if insight is None:
            return "No matching insight", 404
        try:
            db.session.delete(insight)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 409

        return 204

class InsightCollectionByUserItem(Resource):
    """
      Resource for all the insights created by a user, a simple list without much detail
    """
    def get(self, user):
        """
           get all insights created by a user
         """
        try:
            insights = Insight.query.filter_by(creator=user.id).all()
            user_insights = [
                {
                    "id": insight.id,
                    "title": insight.title,
                    "description": insight.description,
                    "longitude": insight.longitude,
                    "latitude": insight.latitude,
                    "category": insight.category,
                    "created_date": insight.created_date.isoformat()
                }
                for insight in (insights if insights else [])
            ]
            return user_insights, 200
        except SQLAlchemyError as e:
            return {"error": str(e)}, 500



class AllInsights(Resource):
    """
       Resource for insights to be displayed on the map. No need to be detailed
    """
    def get(self):
        """
           get all insights with simple content
        """
        try:
            insights = Insight.query.all()
            insight_list = [
                {
                    "id": insight.id,
                    "title": insight.title,
                    "description": insight.description,
                    "longitude": insight.longitude,
                    "latitude": insight.latitude,
                    "category": insight.category,
                }
                for insight in (insights if insights else [])
            ]
            return insight_list, 200
        except SQLAlchemyError as e:
            return   {"error": str(e)}, 500

class InsightItemByUserItem(Resource):
    """
        Resource for single insight created by a user
    """
    def post(self, user):
        """
            create a new insight
        """
        if request.content_type != "application/json":
            raise UnsupportedMediaType

        payload = request.get_json()
        new_insight = Insight(
            creator = user.id,
            title=payload["title"],
            description=payload["description"],
            longitude=payload["longitude"],
            latitude=payload["latitude"],
            image=payload["image"],
            address=payload["address"],
            category=payload["category"],
            subcategory=payload["subcategory"],
            external_link=payload["external_link"],
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
        try:
            db.session.add(new_insight)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 409
        return new_insight, 201
