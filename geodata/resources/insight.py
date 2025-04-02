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
            # 1. Fetch and validate query parameters
            params, error_response = self._parse_and_validate_params()
            if error_response:
                return error_response
            
            # 2. Build and execute the query with given username in the path
            params["username"] = user
            insights = self._fetch_insights(params)

            # 3. Construct the MASON-formatted response body
            body = self._build_insight_collection_response(insights, user)
            body.add_control("up", url_for("api.useritem", user=user.id))

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
        response.headers["Location"] = url_for("api.insightitem", user=user.username, insight=new_insight.id)

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
        body.add_control_user_collection()
        if request.user and request.user.is_authenticated and user == request.user.username:
            body.add_control("up", url_for("api.useritem", user=user.username))
        body["items"] = []

        for i in insights:
            item = GeodataBuilder(i.serialize(short_form=True))
            item["@type"] = "insight"
            item.add_control("self", url_for("api.insightitem", insight=i.id))
            item.add_control("profile", href=INSIGHT_PROFILE_URL)
            body["items"].append(item)

        return body

class InsightItem(Resource):
    """
      Resource for single insight with all the details
    """

    @cache.cached()
    def get(self, insight, user=None):
        """
        Retrieve a single insight by its ID.
        No authentication required. Returns full details.
        """
        # Determine authenticated user via API key
        auth_user = get_authenticated_user()

        body = GeodataBuilder(insight.serialize(short_form=False))
        body["@type"] = "insight"
        body.add_namespace("geometa", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.insightitem", insight=insight.id))
        body.add_control("profile", href=INSIGHT_PROFILE_URL)
        body.add_control_insight_collection(user)
        body.add_control_feedback_collection(user, authuser=None, insight=insight)
        body.add_control_edit_insight(auth_user, insight)
        body.add_control_delete_insight(auth_user, insight)
        body.add_control("author", url_for("api.useritem", user=insight.creator))

        return Response(json.dumps(body), 200, mimetype=MASON)


    def put(self, insight, user=None):
        """
        Update a single insight.
        Only the insight creator or an admin can perform this action.
        """

        # 1. Check authentication
        auth_user = get_authenticated_user()
        if not auth_user:
            return GeodataBuilder.create_error_response(
                401,
                "Unauthorized",
                "You must provide a valid API key to update this insight."
            )

        is_owner = insight.user and insight.user.id == auth_user.id
        is_admin = auth_user.api_key and auth_user.api_key.admin

        if not (is_owner or is_admin):
            return GeodataBuilder.create_error_response(
                403,
                "Forbidden",
                "You do not have permission to update this insight."
            )
        
        # 2. Check content type
        if request.content_type != "application/json":
            return GeodataBuilder.create_error_response(
                415,
                "Unsupported Media Type",
                "Content-Type must be application/json"
            )

        # 3. Validate request body
        try:
            data = request.get_json()
            validate(data, Insight.get_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            return GeodataBuilder.create_error_response(
                400,
                "Invalid request body",
                str(e)
            )
        
        # 4. Perform update
        insight.title = data["title"]
        insight.description = data["description"]
        insight.longitude = data["longitude"]
        insight.latitude = data["latitude"]
        insight.image = data["image"]
        insight.address = data["address"]
        insight.category = data["category"]
        insight.subcategory = data["subcategory"]
        insight.external_link = data["external_link"]

        db.session.commit()

        # 5. Invalidate cache
        cache.delete(request.path)

        # 6. Return updated resource with MASON format (or just 204 if preferred)
        body = GeodataBuilder(insight.serialize(short_form=False))
        body["@type"] = "insight"
        body.add_namespace("geometa", INSIGHT_PROFILE_URL)
        body.add_control("self", url_for("api.insightitem", insight=insight.id))
        body.add_control("profile", href=INSIGHT_PROFILE_URL)
        body.add_control_insight_collection(user)
        body.add_control_feedback_collection(user, authuser=None, insight=insight)
        body.add_control_edit_insight(auth_user, insight)
        body.add_control_delete_insight(auth_user, insight)

        response = Response(json.dumps(body), 200, mimetype=MASON)
        response.headers["Location"] = url_for("api.insightitem", insight=insight.id)
        return response


    def delete(self, insight, user=None):
        """
        Delete a single insight.
        Only the creator of the insight or an admin can delete it.
        """

        # 1. Authenticate the user
        auth_user = get_authenticated_user()
        if not auth_user:
            return GeodataBuilder.create_error_response(
                401,
                "Unauthorized",
                "You must provide a valid API key to delete this insight."
            )

        is_owner = insight.user and insight.user.id == auth_user.id
        is_admin = auth_user.api_key and auth_user.api_key.admin

        if not (is_owner or is_admin):
            return GeodataBuilder.create_error_response(
                403,
                "Forbidden",
                "You do not have permission to delete this insight."
            )

        # 2. Delete the resource
        db.session.delete(insight)
        db.session.commit()

        # 3. Clear cache
        cache.delete(request.path)

        # 4. Return empty success response
        return Response(status=204)
