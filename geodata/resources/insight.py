"""
This module defines insight resource.
"""
import json
from datetime import datetime
from flask import request, Response, url_for
from flask_restful import Resource
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from jsonschema import validate, ValidationError, Draft7Validator
from geodata import db
from geodata.constants import MASON
from geodata.models import Insight

draft7_format_checker = Draft7Validator.FORMAT_CHECKER

class InsightItem(Resource):
    """
      Resource for single insight with all the details
    """
    def get(self, insight):
        """
          Get a single insight by id
        """
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
        try:
            data = request.get_json()
            validate(data, Insight.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

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
        db.session.commit()
        return Response(status=204)

    def delete(self, insight):
        """
          delete a single insight
        """
        db.session.delete(insight)
        db.session.commit()
        return Response(status=204)

class InsightCollectionByUserItem(Resource):
    """
      Resource for all the insights created by a user, a simple list without much detail
    """
    def get(self, user):
        """
           get all insights created by a user
        """
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

        response = {
            "@type": "feedbacks",
            "items": user_insights,
        }

        return response

    def post(self, user):
        """
            create a new insight
        """
        if request.content_type != "application/json":
            raise UnsupportedMediaType

        try:
            data = request.get_json()
            validate(data, Insight.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

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
        db.session.add(new_insight)
        db.session.commit()

        response = Response(status=201)
        response.headers["Location"] = url_for("api.insightitem", insight=new_insight)

        return response

class AllInsights(Resource):
    """
       Resource for insights to be displayed on the map. No need to be detailed
    """
    def get(self):
        """
           get all insights with simple content
        """
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
        response = {
            "@type": "insights",
            "items": insight_list,
        }
        return response



