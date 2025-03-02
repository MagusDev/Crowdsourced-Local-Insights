from datetime import datetime

from flask import Flask, Response, request, jsonify
from flask_restx import Resource
from werkzeug.exceptions import UnsupportedMediaType
from sqlalchemy.exc import IntegrityError

from geodata import db
from geodata.models import Insight

# Single insight with all the details
class InsightItem(Resource):
    def get(self, insight):
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
        "created_date": insight.created_date,
        "modified_date": insight.modified_date,
        "creator": insight.creator,
        "category": insight.category,
        "subcategory": insight.subcategory,
        "external_link": insight.external_link,
        "address": insight.address
      }
      return response, 200

    def put(self, insight):
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

# All the insights created by a user, a simple list without much detail
class InsightCollectionByUserItem(Resource):

    def get(self, user):
        try:
            insights = Insight.query.filter_by(creator=user).all()
            user_insights = [
                {
                    "id": insight.id,
                    "title": insight.title,
                    "description": insight.description,
                    "longitude": insight.longitude,
                    "latitude": insight.latitude,
                    "category": insight.category,
                    "created_date": insight.created_date
                }
                for insight in (insights if insights else [])
            ]
            return user_insights, 200
        except Exception as e:
            return {"error": str(e)}, 500


# Insights to be displayed on the map. No need to be detailed
class AllInsights(Resource):

    def get(self):
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
        except Exception as e:
            return   {"error": str(e)}, 500
