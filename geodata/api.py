from flask import Blueprint
from flask_restx import Api
from .resources.user import UserCollection, UserItem
from .resources.insight import InsightCollectionByUserItem, InsightItemByUserItem, AllInsights
from .resources.feedback import (
    FeedbackCollectionByUserInsightItem,
      FeedbackCollectionByUserItem,
        FeedbackItemByUserInsightItem
)

api_bp = Blueprint("api", __name__, url_prefix="/api")
# GPT used to set swagger
api = Api(api_bp, doc="/swagger")

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(InsightCollectionByUserItem, "/users/<user:user>/insights/")
api.add_resource(FeedbackCollectionByUserItem, "/users/<user:user>/feedbacks/")
api.add_resource(InsightItemByUserItem, "/users/<user:user>/insights/<insight:insight>/")
api.add_resource(
    FeedbackCollectionByUserInsightItem,
      "/users/<user:user>/insights/<insight:insight>/feedbacks/")
api.add_resource(
    FeedbackItemByUserInsightItem,
      "/users/<user:user>/insights/<insight:insight>/feedbacks/<feedback:feedback>/")
api.add_resource(AllInsights, "/insights/")
