"""
This module set api resource route.
"""
from .api_init import api
from .resources.user import UserCollection, UserItem
from .resources.insight import InsightCollectionByUserItem, AllInsights, InsightItemByUserItem
from .resources.feedback import (
    FeedbackCollectionByUserInsightItem,
      FeedbackCollectionByUserItem,
        FeedbackItemByUserInsightItem
)

api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(FeedbackCollectionByUserItem, "/users/<user:user>/feedbacks/")
api.add_resource(InsightCollectionByUserItem, "/users/<user:user>/insights/")
api.add_resource(InsightItemByUserItem, "/users/<user:user>/insight/")
api.add_resource(AllInsights, "/insights/")
api.add_resource(
    FeedbackCollectionByUserInsightItem,
      "/users/<user:user>/insights/<insight:insight>/feedbacks/")
api.add_resource(
    FeedbackItemByUserInsightItem,
      "/users/<user:user>/insights/<insight:insight>/feedbacks/<feedback:feedback>/")
