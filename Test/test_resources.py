"""
This module is used to prepare test resources.
"""
import base64
import random
import tempfile
import os
import sys
from datetime import datetime
from urllib.parse import quote
import pytest
from geodata import db, create_app
from geodata.models import User, Insight, Feedback



@pytest.fixture
def client():
    """
    Create test client
    """
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True,
    }
    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_db()

        yield app.test_client()

        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    try:
        os.unlink(db_fname)
    except:
        pass


# generated test data with claude sonnet
def _populate_db():
    """
    Populate the test database with sample data including users, insights, and feedback.
    """
    test_users = [
        User(
            username="testuser1",
            email="testuser1@example.com",
            password=User().hash_password("password123"),
            first_name="Test",
            last_name="User1",
        ),
        User(
            username="testuser2",
            email="testuser2@example.com",
            password=User().hash_password("password123"),
            first_name="Test",
            last_name="User2",
        ),
        User(
            username="admin",
            email="admin@example.com",
            password=User().hash_password("adminpass"),
            first_name="Admin",
            last_name="User",
            role="ADMIN"
        )
    ]

    db.session.add_all(test_users)
    db.session.commit()


    test_insights = [
        Insight(
            title="Coffee Shop Recommendation",
            description="Great coffee shop with free WiFi and quiet atmosphere",
            longitude=25.473,
            latitude=65.012,
            created_date= datetime.utcnow(),
            modified_date= datetime.utcnow(),
            creator=test_users[0].id,
            category="Food & Drink",
            subcategory="Cafe",
            address="123 Test Street, Oulu"
        ),
        Insight(
            title="Beautiful Park",
            description="Peaceful park with walking trails and playground",
            longitude=25.469,
            latitude=65.009,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            creator=test_users[1].id,
            category="Outdoor",
            subcategory="Park",
            address="456 Park Avenue, Oulu"
        ),
        Insight(
            title="Free Parking Area",
            description="Always available parking spots, even during rush hours",
            longitude=25.465,
            latitude=65.014,
            created_date= datetime.utcnow(),
            modified_date=datetime.utcnow(),
            creator=test_users[0].id,
            category="Infrastructure",
            subcategory="Parking",
            address="789 Main Street, Oulu"
        )
    ]

    db.session.add_all(test_insights)
    db.session.commit()

    test_feedback = [
        Feedback(
            user_id=test_users[1].id,
            insight_id=test_insights[0].id,
            rating=5,
            comment="Really useful insight! I found this place because of you."
        ),
        Feedback(
            user_id=test_users[0].id,
            insight_id=test_insights[1].id,
            rating=4,
            comment="Nice park, good for relaxing"
        ),
        Feedback(
            user_id=test_users[2].id,
            insight_id=test_insights[0].id,
            rating=3,
            comment="Average place, coffee was just ok"
        )
    ]

    db.session.add_all(test_feedback)
    db.session.commit()

def get_user_json(number =1):
    """
    Generate user JSON data
    """
    return {
        "username": f"extrauser{number}",
        "email": f"extrauser{number}@example.com",
        "password": "password123",
        "first_name": "Extra",
        "last_name": "User",
        "status": "ACTIVE",
        "role": "USER",
    }


def get_api_key_header(client, number=99):
    """Create a user and get API key header"""
    user_data = get_user_json(number)  # Use a unique number
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == 201
    api_key = response.get_json()["api_key"]
    return {
        "Authorization": f"Bearer {api_key}",  # Changed from "Geodata-Api-Key"
        "user": user_data["username"]
    }


class TestUsersCollection():
    """
    Test user collection
    """
    RESOURCE_URL = "/api/users/"
    def test_get(self, client):
        """
        Test get users
        """
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 3
        usernames = [item["username"] for item in body["items"]]
        assert set(usernames) == {"testuser1", "testuser2", "admin"}

    def test_post(self, client):
        """
        Test create user
        """

        response = client.post(self.RESOURCE_URL, data= "not json")
        assert response.status_code in [400, 415]


        valid_user = get_user_json()
        response = client.post(self.RESOURCE_URL, json=valid_user)
        assert response.status_code == 201
        assert response.headers["Location"] == "/api/users/" + valid_user["username"] + "/"
        response = client.get(response.headers["Location"])
        assert response.status_code == 200

        response = client.post(self.RESOURCE_URL, json=valid_user)
        assert response.status_code == 409

        valid_user.pop("email")
        response = client.post(self.RESOURCE_URL, json=valid_user)
        assert response.status_code == 400

class TestUserItem():
    """
    Test user
    """
    RESOURCE_URL = "/api/users/testuser1/"
    INVALID_URL = "/api/users/invaliduser/"

    def test_get(self, client):
        """
        Test get user
        """
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert body["username"] == "testuser1"

        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_put(self, client):
        """
        Test update user
        """

        api_key_info = get_api_key_header(client)
        username = api_key_info["user"]
        resource_url = f"/api/users/{username}/"
        headers = {"Authorization": api_key_info["Authorization"]}
        valid_user = get_user_json(3)
        valid_user["username"] = username
        valid_user["status"] = "ACTIVE"
        valid_user["role"] = "USER"

        response = client.put(resource_url, headers = headers, data= "not json")
        assert response.status_code in [400, 415]

        response = client.put(self.INVALID_URL, headers = headers, json=valid_user)
        assert response.status_code == 404


        conflict_user = valid_user.copy()
        conflict_user["username"] = "testuser2"
        response = client.put(
            resource_url,
            json=conflict_user,
            headers= headers)
        assert response.status_code == 409

        response = client.put(resource_url, headers=headers, json=valid_user)
        assert response.status_code == 204

        invalid_headers = {"Authorization": "Bearer invalid_key"}
        response = client.put(resource_url, headers=invalid_headers, json=valid_user)
        assert response.status_code == 403

        invalid_user = valid_user.copy()
        invalid_user.pop("email")
        response = client.put(resource_url, headers=headers, json=invalid_user)
        assert response.status_code == 400

    def test_delete(self, client):
        """
        Test delete user
        """
        # Create a test user with API key
        api_key_info = get_api_key_header(client)
        username = api_key_info["user"]
        resource_url = f"/api/users/{username}/"
        headers = {"Authorization": api_key_info["Authorization"]}

        response = client.delete(resource_url)
        assert response.status_code == 403

        response = client.delete(self.INVALID_URL, headers=headers)
        assert response.status_code == 404

        invalid_headers = {"Authorization": "Bearer invalid_key"}
        response = client.delete(resource_url, headers=invalid_headers)
        assert response.status_code == 403

        response = client.delete(resource_url, headers=headers)
        assert response.status_code == 204

        response = client.delete(resource_url, headers=headers)
        assert response.status_code == 404

class TestFeedbackCollectionByUserInsightItem():
    """
    Test feedback collection by user insight
    """
    RESOURCE_URL = "/api/users/testuser2/insights/1/feedbacks/"
    INVALID_URL = "/api/users/testuser2/insights/100/feedbacks/"

    def test_get(self, client):
        """
        Test get feedback collection by user insight
        """
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 1

        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_post(self, client):
        """
        Test post feedback
        """
        response = client.post(self.RESOURCE_URL, data= "not json")
        assert response.status_code in [400, 415]

        response = client.post(self.INVALID_URL, json={"rating": 5, "comment": "Great insight!"})
        assert response.status_code == 404

        response = client.post(self.RESOURCE_URL, json={"rating": 5, "comment": "Great insight!"})
        assert response.status_code == 201
        assert response.headers["Location"] == "/api/users/testuser2/insights/1/feedbacks/4/"
        response = client.get(response.headers["Location"])
        assert response.status_code == 200

        response = client.post(
            self.RESOURCE_URL,
            json={"rating": "nice", "comment": "Great insight!"}
            )
        assert response.status_code == 400

class TestFeedbackCollectionByUserItem():
    """
    Test feedback collection by user
    """
    RESOURCE_URL = "/api/users/testuser2/feedbacks/"
    def test_get(self, client):
        """
        Test get feedback collection
        """
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 1

class TestFeedbackItemByUserInsightItem():
    """
    Test feedback item by user and insight
    """
    RESOURCE_URL = "/api/users/testuser2/insights/1/feedbacks/1/"
    INVALID_URL = "/api/users/testuser2/insights/1/feedbacks/100/"

    def test_get(self, client):
        """
              Test get feedback items by user insight
        """
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200

        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_put(self, client):
        """
        Test update feedback items by user insight
        """
        valid_feedback = {
            "rating": 4,
            "comment": "nice insight!"
        }
        response = client.put(self.RESOURCE_URL, data= "not json")
        assert response.status_code in [400, 415]

        response = client.put(self.INVALID_URL, json=valid_feedback)
        assert response.status_code == 404

        valid_feedback["rating"] = "nice"
        response = client.put(self.RESOURCE_URL, json=valid_feedback)
        assert response.status_code == 400

        valid_feedback["rating"] = 4
        response = client.put(self.RESOURCE_URL, json=valid_feedback)
        assert response.status_code == 204



    def test_delete(self, client):
        """
           Test delete feedback items by user insight.
        """
        response = client.delete(self.INVALID_URL)
        assert response.status_code == 404

        response = client.delete(self.RESOURCE_URL)
        assert response.status_code == 204

        response = client.delete(self.RESOURCE_URL)
        assert response.status_code == 404

class TestInsightItem:
    """Tests for the InsightItem resource (GET, PUT, DELETE)"""
    RESOURCE_URL = "/api/insights/1/"
    INVALID_URL = "/api/insights/100/"

    def test_get(self, client):
        """Test retrieving insight details - no auth required"""
        # Valid insight
        response = client.get(self.RESOURCE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert body["@type"] == "insight"
        assert "title" in body and "longitude" in body and "latitude" in body
        
        # Invalid insight
        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_put_unauthorized(self, client):
        """Test updating insight with unauthorized scenarios"""
        valid_insight = {
            "title": "Updated Title",
            "description": "Updated Description",
            "longitude": 25.473,
            "latitude": 65.012,
            "category": "Food & Drink"
        }
        
        # No auth - should fail
        response = client.put(self.RESOURCE_URL, json=valid_insight)
        assert response.status_code == 401
        
        # Non-owner auth - should fail
        api_key_info = get_api_key_header(client)
        headers = {"Authorization": api_key_info["Authorization"]}
        response = client.put(self.RESOURCE_URL, headers=headers, json=valid_insight)
        assert response.status_code == 403

    def test_put_and_delete_own_insight(self, client):
        """Test updating and deleting user's own insight"""
        # 1. Create a new user
        test_user = {
            "username": "insightowner",
            "email": "insightowner@example.com",
            "password": "password123",
            "first_name": "Insight",
            "last_name": "Owner"
        }
        response = client.post("/api/users/", json=test_user)
        assert response.status_code == 201
        user_data = response.get_json()
        user_key = user_data["api_key"]
        headers = {"Authorization": f"Bearer {user_key}"}
        
        # 2. User creates their own insight
        new_insight = {
            "title": "Owner's Test Insight",
            "description": "Created to test PUT and DELETE",
            "longitude": 25.5,
            "latitude": 65.0,
            "category": "Test",
            "subcategory": "Testing"
        }
        
        response = client.post(f"/api/users/insightowner/insights/", 
                              headers=headers, 
                              json=new_insight)
        assert response.status_code == 201
        insight_url = response.headers["Location"]
        
        # 3. User updates their own insight
        updated_insight = new_insight.copy()
        updated_insight["title"] = "Updated Owner's Insight"
        updated_insight["description"] = "Updated description"
        
        response = client.put(insight_url, headers=headers, json=updated_insight)
        assert response.status_code == 200
        
        # 4. Verify update worked
        response = client.get(insight_url)
        assert response.status_code == 200
        body = response.get_json()
        assert body["title"] == "Updated Owner's Insight"
        assert body["description"] == "Updated description"
        
        # 5. Test invalid update formats
        response = client.put(insight_url, headers=headers, data="not json")
        assert response.status_code == 415
        
        invalid_insight = updated_insight.copy()
        invalid_insight.pop("title")  # Remove required field
        response = client.put(insight_url, headers=headers, json=invalid_insight)
        assert response.status_code == 400
        
        # 6. User deletes their own insight
        response = client.delete(insight_url, headers=headers)
        assert response.status_code == 204
        
        # 7. Verify deletion worked
        response = client.get(insight_url)
        assert response.status_code == 404

    def test_delete_unauthorized(self, client):
        """Test unauthorized delete scenarios"""
        # No auth
        response = client.delete(self.RESOURCE_URL)
        assert response.status_code == 401
        
        # With auth but not owner
        api_key_info = get_api_key_header(client)
        headers = {"Authorization": api_key_info["Authorization"]}
        
        # User can't delete others' insights
        response = client.delete(self.RESOURCE_URL, headers=headers)
        assert response.status_code == 403

class TestInsightCollection():
    """
    Test for insights collection with filtering capabilities
    """
    
    def test_get_with_filters(self, client):
        """
        Test getting insights with various query filters
        """
        # Test with no filters (should return error since filters are required)
        response = client.get("/api/insights/")
        assert response.status_code == 400  # or 400 if you want to require filters
        
        # Test with bbox parameter
        response = client.get("/api/insights/?bbox=25.4,65.0,25.5,65.1")
        assert response.status_code == 200
        body = response.get_json()
        assert "items" in body
        assert len(body["items"]) > 0
        
        # Test with username parameter
        response = client.get("/api/insights/?usr=testuser1")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 2
        
        # Test with category filter
        response = client.get("/api/insights/?usr=testuser1&ic=Food+%26+Drink")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 1
        assert body["items"][0]["category"] == "Food & Drink"
        
        # Test with subcategory filter
        response = client.get("/api/insights/?bbox=0,0,90,90&ic=Infrastructure&isc=Parking")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 1
        assert body["items"][0]["category"] == "Infrastructure"
        
        # Test with invalid bbox format
        response = client.get("/api/insights/?bbox=invalid")
        assert response.status_code == 400
        
        # Test with non-existent user
        response = client.get("/api/insights/?usr=nonexistentuser")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 0
        
    def test_get_by_user_path(self, client):
        """
        Test getting insights via the user path
        """
        # Test getting insights by valid user
        response = client.get("/api/users/testuser1/insights/")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 2  # testuser1 has 2 insights
        
        # Test getting insights by admin user
        response = client.get("/api/users/admin/insights/")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 0  # admin has no insights
        
        # Test getting insights by invalid user
        response = client.get("/api/users/nonexistentuser/insights/")
        assert response.status_code == 404
        
        # Test with additional filters on user path
        response = client.get("/api/users/testuser1/insights/?ic=Infrastructure")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 1  # testuser1 has 1 Infrastructure insight


    def test_post(self, client):
        """
        Test creating insights through both anonymous and user-specific endpoints
        """
        # 1. Test anonymous insight creation (global endpoint)
        anon_insight = {
            "title": "Anonymous Insight",
            "description": "Created without authentication",
            "longitude": 25.5,
            "latitude": 65.1,
            "category": "Anonymous",
            "subcategory": "Testing"
        }
        
        response = client.post("/api/insights/", json=anon_insight)
        # If anonymous posting is allowed:
        assert response.status_code == 201
        assert "Location" in response.headers
        insight_url = response.headers["Location"]
        # Verify the insight was created
        response = client.get(insight_url)
        assert response.status_code == 200
        body = response.get_json()
        assert body["title"] == anon_insight["title"]
        assert body["user"] is None  # Should be anonymous

        
        # 2. Test user-specific insight creation
        api_key_info = get_api_key_header(client, number= 7)  
        headers = {"Authorization": api_key_info["Authorization"]}
        username = api_key_info["user"]
        user_insight = {
            "title": "User's Insight",
            "description": "Created via user-specific endpoint",
            "longitude": 25.473,
            "latitude": 65.012,
            "category": "Testing",
            "subcategory": "API"
        }
        
     
        # Use the user-specific endpoint
        response = client.post(f"/api/users/{username}/insights/", 
                              headers=headers, 
                              json=user_insight)
        assert response.status_code == 201
        assert "Location" in response.headers
        insight_url = response.headers["Location"]
        
        # Verify the insight was created and attributed to the user
        response = client.get(insight_url)
        assert response.status_code == 200
        body = response.get_json()
        assert body["title"] == user_insight["title"]
        assert body["user"] == username
        
        # 3. Test validation failures
        # Missing required field
        invalid_insight = user_insight.copy()
        invalid_insight.pop("title")
        response = client.post(f"/api/users/{username}/insights/", 
                              headers=headers, 
                              json=invalid_insight)
        assert response.status_code == 400
        
        # Invalid content type
        response = client.post(f"/api/users/{username}/insights/", 
                              headers=headers, 
                              data="not json")
        assert response.status_code in [400, 415]
