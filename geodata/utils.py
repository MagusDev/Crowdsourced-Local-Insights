from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from .models import User, Insight

class UserConverter(BaseConverter):

    def to_python(self, user):
        db_user = User.query.filter(or_(User.username == user, User.email == user)).first()
        if db_user is None:
            raise NotFound
        return db_user
    
    def to_url(self, db_user):
        return db_user.username
    

class InsightConverter(BaseConverter):

    def to_python(self, insight_uuid):
        db_insight = Insight.query.filter_by(Insight.id == insight_uuid).first()
        if db_insight is None:
            raise NotFound
        return db_insight
    
    # TODO: Check the implementation of this
    def to_url(self, db_insight):
        return db_insight.user + "/insights/" + db_insight.id