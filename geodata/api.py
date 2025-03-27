"""
This module set api resource route.
"""
from .api_init import api
from .resources.user import UserCollection, UserItem
from .resources.insight import InsightCollectionByUserItem, AllInsights, InsightItem
from .resources.feedback import (
    FeedbackCollectionByUserInsightItem,
      FeedbackCollectionByUserItem,
        FeedbackItemByUserInsightItem
)

api.add_resource(InsightCollection, "/insights/", endpoint="insights")
api.add_resource(InsightCollection, "/users/<user>/insights/", endpoint="insights_by")
api.add_resource(InsightItem, "/insights/<insight>/", endpoint="insight")
api.add_resource(InsightItem, "/users/<user>/insights/<insight>/", endpoint="insight_by")
api.add_resource(FeedbackCollection, "/users/<user>/insights/<insight>/feedbacks/", endpoint="feedbacks_by_insight")
api.add_resource(FeedbackCollection, "/users/<user>/feedbacks/", endpoint="feedbacks_by_user")
api.add_resource(FeedbackItem, "/users/<user>/feedbacks/<feedback>/", endpoint="feedback_by_user")
api.add_resource(FeedbackItem, "/users/<user>/insights/<insight>/feedbacks/<feedback>/", endpoint="feedback_by_insight")
api.add_resource(UserCollection, "/users/", endpoint="users")
api.add_resource(UserItem, "/users/<user>/", endpoint="user")
