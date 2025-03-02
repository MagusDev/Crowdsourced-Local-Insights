from flask import Flask, Response, request, jsonify
from flask_restx import Resource
from werkzeug.exceptions import UnsupportedMediaType

from geodata import db
from geodata.models import Insight

# Single insight with all the details
class InsightItem(Resource):

    def get(self, insight):
      insight = Insight.query.filter_by(id=insight.id).first()
      if insight is None:
        return Response(status=404)
      response = {
        "id": insight.id,
        "title": insight.title,
        "description": insight.description,
        "longitude": insight.longitude,
        "latitude": insight.latitude,
        "image": insight.image,
        "created_date": insight.created_date,
        "modified_date": insight.modified_date,
        "creator": insight.creator, # Should show user name instead of id
        "category": insight.category,
        "subcategory": insight.subcategory,
        "external_link": insight.external_link,
        "address": insight.address,
        #user
        #feedback
      }
      return jsonify(response)

class InsightCollectionByUserItem(Resource):

    def delete(self, insight):
        insight = Insight.query.filter_by(id=insight.id).first()
        if insight is None:
            return Response(status=404)
        db.session.delete(insight)
        db.session.commit()
        return Response(status=204)

    def put(self, insight):
        if request.content_type != "application/json":
            raise UnsupportedMediaType
        payload = request.get_json()
        insight




# All the insights created by a user
class InsightCollectionByUserItem(Resource):

    def get(self, user):
        pass

    def delete(self, insight):
        pass
    def post(self, user):
        pass

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


# class InsightItemByUserItem(Resource):
#
#     def get(self, insight):
#         pass
#
#     def put(self, insight):
#         pass
#
#     def delete(self, insight):
#         pass
