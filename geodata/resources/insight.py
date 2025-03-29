"""
This module defines insight resource.
"""
import json
from datetime import datetime
from flask import request, Response, url_for
from flask_restful import Resource
from werkzeug.exceptions import UnsupportedMediaType, BadRequest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload
from jsonschema import validate, ValidationError, Draft7Validator
from constants import *
from geodata import db
from geodata.auth import require_admin, require_user_auth, get_authenticated_user
from geodata.constants import MASON
from geodata.models import Insight, User
from geodata.utils import GeodataBuilder
from geodata import cache

draft7_format_checker = Draft7Validator.FORMAT_CHECKER

class InsightItem(Resource):
    """
      Resource for single insight with all the details
    """
    @cache.cached()
    def get(self, insight, user=None):
        """
          Get a single insight by id
        """
        response = {
            "id": insight.id,
            "title": insight.title,
            "description": insight.description,
            "longitude": insight.longitude,
            "latitude": insight.latitude,
            "image": insight.image,
            "created_date": insight.created_date.isoformat(),
            "modified_date": insight.modified_date.isoformat(),
            "creator": insight.creator,
            "category": insight.category,
            "subcategory": insight.subcategory,
            "external_link": insight.external_link,
            "address": insight.address
        }
        return response, 200

    def put(self, insight):
        """
          Update a single insight
        """
        if request.content_type != "application/json":
            raise UnsupportedMediaType
        try:
            data = request.get_json()
            validate(data, Insight.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        payload = request.get_json()
        updated_insight = Insight.query.filter_by(id=insight.id).first()
        updated_insight.title = payload["title"]
        updated_insight.description = payload["description"]
        updated_insight.longitude = payload["longitude"]
        updated_insight.latitude = payload["latitude"]
        updated_insight.image = payload["image"]
        updated_insight.address = payload["address"]
        updated_insight.category = payload["category"]
        updated_insight.subcategory = payload["subcategory"]
        updated_insight.external_link = payload["external_link"]
        db.session.commit()

        cache.delete(request.path)

        return Response(status=204)

    def delete(self, insight):
        """
          delete a single insight
        """
        db.session.delete(insight)
        db.session.commit()

        cache.delete(request.path)

        return Response(status=204)

class InsightCollection(Resource):
    """
      Resource for all the insights, a simple list without much detail
    """

    def get(self, user=None):
        """
        Retrieve all insights that match the given filters OR
        if user exist it will retrieve all insights by that user.

        At least one of the following query parameters must be provided:
        - 'bbox': bounding box of the search area (format: minLon,minLat,maxLon,maxLat)
        - 'usr': creator's username

        Optional filters:
        - 'ic': insight category
        - 'isc': insight subcategory

        Returns a MASON-formatted collection of insights with basic information
        and hypermedia controls for navigation and interaction.
        """
        if user:
            # 1. Build and execute the query with given username
            insights = self._fetch_insights({"username": user})

            # 2. Construct the MASON-formatted response body
            body = self._build_insight_collection_response(insights, user)

            return Response(json.dumps(body), 200, mimetype=MASON)
        else: 
            # 1. Fetch and validate query parameters
            params, error_response = self._parse_and_validate_params()
            if error_response:
                return error_response

            # 2. Build and execute the query with given parameters
            insights = self._fetch_insights(params)

            # 3. Construct the MASON-formatted response body
            body = self._build_insight_collection_response(insights)

            return Response(json.dumps(body), 200, mimetype=MASON)


    def post(self, user=None):
        """
        Create a new insight.

        If a username is provided in the path, the request must include a valid
        API key via Authorization: Bearer <token>, and the key must belong to that user.

        If no username is provided, the insight can be added anonymously.
        """

        # Require content-type to be JSON
        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415,
                "Unsupported Media Type",
                "Content-Type must be application/json"
            )

        # Determine authenticated user via API key
        auth_user = get_authenticated_user()

        if user:
            # Auth required: user must be authenticated and match path user
            if not auth_user:
                return GeodataBuilder.create_error_response(
                    403,
                    "Authentication required",
                    "You must authenticate to post as a user."
                )

            if auth_user.username != user:
                return GeodataBuilder.create_error_response(
                    403,
                    "Forbidden",
                    "You are not allowed to post as another user."
                )
            creator_id = auth_user.id
        else:
            # Anonymous posting
            creator_id = None

        # Validate request body against schema
        try:
            data = request.get_json()
            validate(data, Insight.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(
                400,
                "Invalid request data",
                str(e)
            )
        
        # Create new Insight
        new_insight = Insight(
            creator=creator_id,
            title=data["title"],
            description=data.get("description"),
            longitude=data["longitude"],
            latitude=data["latitude"],
            image=data.get("image"),
            address=data.get("address"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            external_link=data.get("external_link"),
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

        db.session.add(new_insight)
        db.session.commit()

        response = Response(status=201)
        response.headers["Location"] = url_for("api.insightitem", insight=new_insight.id)

        return response


    def _parse_and_validate_params(self):
        bbox = request.args.get("bbox")
        username = request.args.get("usr")
        category = request.args.get("ic")
        subcategory = request.args.get("isc")

        # At least bbox or username is required
        if not bbox and not username:
            return None, GeodataBuilder.create_error_response(
                400,
                "Missing bbox or username",
                "Provide at least one of: bbox or usr"
            )

        # Try parsing the bbox if provided
        try:
            if bbox:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
            else:
                min_lon = min_lat = max_lon = max_lat = None
        except ValueError:
            return None, GeodataBuilder.create_error_response(
                400,
                "Invalid bbox format",
                "Expected format: bbox=25.4,65.0,25.6,65.1"
            )

        return {
            "bbox": (min_lon, min_lat, max_lon, max_lat) if bbox else None,
            "username": username.lower() if username else None,
            "category": category.lower() if category else None,
            "subcategory": subcategory.lower() if subcategory else None
        }, None
    

    def _fetch_insights(self, params):
        query = Insight.query

        # Filter by bounding box
        if params["bbox"]:
            min_lon, min_lat, max_lon, max_lat = params["bbox"]
            query = query.filter(
                Insight.longitude.between(min_lon, max_lon),
                Insight.latitude.between(min_lat, max_lat)
            )

        # Filter by creator's username
        if params["username"]:
            query = query.join(User).filter(User.username == params["username"])

        # Filter by category
        if params["category"]:
            query = query.filter(Insight.category == params["category"])

        # Filter by subcategory
        if params["subcategory"]:
            query = query.filter(Insight.subcategory == params["subcategory"])

        # Eager load the user relationship to avoid N+1 problem
        query = query.options(joinedload(Insight.user))

        return query.all()
    

    def _build_insight_collection_response(self, insights, user=None):
        body = GeodataBuilder()
        body["@type"] = "insights"
        body.add_control("self", url_for("api.insightcollection"))
        body.add_control_add_insight()
        if request.user and request.user.is_authenticated and user == request.user.username:
            body.add_control_insights_by(user)
            body.add_control("author", url_for("api.useritem", user=user))
        body["items"] = []

        for i in insights:
            item = GeodataBuilder(i.serialize(short_form=True))
            item["@type"] = "insight"
            item.add_control("self", url_for("api.insightitem", insight=i.id))
            item.add_control("profile", href=INSIGHT_PROFILE_URL)
            body["items"].append(item)

        return body
