from flask import Blueprint
from flask_restx import Api
from geodata.resources.feedback import FeedbackCollectionByUserItem, FeedbackCollectionByUserInsightItem, \
    FeedbackItemByUserInsightItem
from geodata.resources.insight import InsightCollectionByUserItem, AllInsights
from geodata.resources.user import UserCollection, UserItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
# GPT used to set swagger
api = Api(api_bp, doc="/swagger")

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(InsightCollectionByUserItem, "/users/<user:user>/insights/")
api.add_resource(FeedbackCollectionByUserItem, "/users/<user:user>/feedbacks/")
api.add_resource(FeedbackCollectionByUserInsightItem, "/users/<user:user>/insights/<insight:insight>/feedbacks/")
api.add_resource(FeedbackItemByUserInsightItem,
                 "/users/<user:user>/insights/<insight:insight>/feedbacks/<feedback:feedback>/")

api.add_resource(AllInsights, "/insights/")