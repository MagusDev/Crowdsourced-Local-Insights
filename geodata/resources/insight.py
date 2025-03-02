from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


class InsightCollectionByUserItem(Resource):

    def get(self, user):
        pass

    def post(self, user):
        pass


class InsightItemByUserItem(Resource):

    def get(self, insight):
        pass

    def put(self, insight):
        pass

    def delete(self, insight):
        pass

class AllInsights(Resource):

    def get(self):
        pass
