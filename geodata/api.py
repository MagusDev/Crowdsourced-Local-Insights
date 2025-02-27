from flask import Blueprint
from flask_restful import Api

from resources.user import UserCollection, UserItem
from resources.insight import InsightCollectionByVariousUsers, InsightCollectionByUserItem, InsightItemByUserItem
from resources.feedback import FeedbackCollectionByInsightItem


api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(InsightCollectionByVariousUsers, "/users/<users:users>/insights/")
api.add_resource(InsightCollectionByUserItem, "/users/<user:user>/insights/")
api.add_resource(InsightItemByUserItem, "/users/<user:user>/insights/<insight:insight>/")
api.add_resource(FeedbackCollectionByInsightItem, "/users/<user:user>/insights/<insight:insight>/feedbacks")