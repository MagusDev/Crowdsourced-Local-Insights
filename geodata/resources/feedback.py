from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


class FeedbackCollectionByInsightItem(Resource):

    def get(self, insight):
        pass