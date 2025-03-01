from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


class FeedbackCollectionByInsightItem(Resource):

    def get(self):
        pass

    def post(self, insight):
        pass

class FeedbackCollectionByUserItem(Resource):

    def get(self, user):
        pass

class FeedbackItemByInsightItem(Resource):

    def get(self):
        pass

    def put(self, feedback):
        pass

    def delete(self, feedback):
        pass