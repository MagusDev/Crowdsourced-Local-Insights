"""
This module set api resource route.
"""
from .api_init import api
from .resources.user import UserCollection, UserItem
from .resources.insight import InsightCollection, InsightItem
from .resources.feedback import FeedbackCollection, FeedbackItem

api.add_resource(InsightCollection, "/insights/", endpoint="insights")
api.add_resource(InsightCollection, "/users/<user:user>/insights/", endpoint="insights_by")
api.add_resource(InsightItem, "/insights/<insight:insight>/", endpoint="insight")
api.add_resource(InsightItem, "/users/<user:user>/insights/<insight:insight>/", endpoint="insight_by")
api.add_resource(FeedbackCollection, "/users/<user:user>/insights/<insight:insight>/feedbacks/", endpoint="feedbacks_by_insight")
api.add_resource(FeedbackCollection, "/users/<user:user>/feedbacks/", endpoint="feedbacks_by_user")
api.add_resource(FeedbackItem, "/users/<user:user>/feedbacks/<feedback:feedback>/", endpoint="feedback_by_user")
api.add_resource(FeedbackItem, "/users/<user:user>/insights/<insight:insight>/feedbacks/<feedback:feedback>/", endpoint="feedback_by_insight")
api.add_resource(UserCollection, "/users/", endpoint="users")
api.add_resource(UserItem, "/users/<user:user>/", endpoint="user")