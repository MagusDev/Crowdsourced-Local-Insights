from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

from resources.user import UserCollection, UserItem
from resources.insight import InsightCollectionByUserItem, InsightItemByUserItem, AllInsights
from resources.feedback import FeedbackCollectionByInsightItem, FeedbackCollectionByUserItem, FeedbackItemByInsightItem

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(InsightCollectionByUserItem, "/users/<user:user>/insights/")
api.add_resource(FeedbackCollectionByUserItem, "/users/<user:user>/feedbacks/")
api.add_resource(InsightItemByUserItem, "/users/<user:user>/insights/<insight:insight>/")
api.add_resource(FeedbackCollectionByInsightItem, "/users/<user:user>/insights/<insight:insight>/feedbacks/")
api.add_resource(FeedbackItemByInsightItem, "/users/<user:user>/insights/<insight:insight>/feedbacks/<feedback:feedback>/")
api.add_resource(AllInsights, "/insights/")