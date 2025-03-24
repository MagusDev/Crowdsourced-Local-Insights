"""
This module is used to prepare test resources.
"""
import base64
import tempfile
import os
import sys
from datetime import datetime

import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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


def get_auth_header(username, password):
    """Generate Basic Auth header"""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

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
        valid_user = get_user_json(3)
        auth_header = get_auth_header("testuser1", "password123")

        response = client.put(self.RESOURCE_URL, headers = auth_header, data= "not json")
        assert response.status_code in [400, 415]

        response = client.put(self.INVALID_URL, headers = auth_header, json=valid_user)
        assert response.status_code == 404

        valid_user["username"] = "testuser2"
        response = client.put(self.RESOURCE_URL, headers = auth_header, json=valid_user)
        assert response.status_code == 409

        valid_user["username"] = "testuser1"
        response = client.put(
            self.RESOURCE_URL,
            json=valid_user,
            headers= auth_header)
        assert response.status_code == 204

        valid_user["username"] = "testuser1"
        response = client.put(
            self.RESOURCE_URL,
            json=valid_user,
            headers= get_auth_header("testuser1", "wrongpassword"))
        assert response.status_code == 401

        valid_user.pop("email")
        response = client.put(self.RESOURCE_URL, headers = auth_header, json=valid_user)
        assert response.status_code == 400

    def test_delete(self, client):
        """
        Test delete user
        """
        response = client.delete(self.RESOURCE_URL)
        assert response.status_code == 401

        response = client.delete(self.INVALID_URL)
        assert response.status_code == 404

        auth_header = get_auth_header("testuser1", "wrongpassword")
        response = client.delete(self.RESOURCE_URL , headers = auth_header)
        assert response.status_code == 401

        auth_header = get_auth_header("testuser1", "password123")
        response = client.delete(self.RESOURCE_URL , headers = auth_header)
        assert response.status_code == 204

        response = client.delete(self.RESOURCE_URL , headers = auth_header)
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

class TestInsightItem():
    """
    Test for single insight with all the details
    """
    def test_get(self, client):
        """
        Test get insight detail with insight id
        """
        response = client.get("/api/insights/1/")
        assert response.status_code == 200

        response = client.get("/api/insights/100/")
        assert response.status_code == 404

    def test_put(self, client):
        """
        Test update insight with insight id
        """
        valid_insight = {
            "title": "New Title",
            "description": "New Description",
            "longitude": 25.473,
            "latitude": 65.012,
            "image": "newimage.jpg",
            "address": "123 Test Street, Oulu",
            "category": "Food & Drink",
            "subcategory": "Cafe",
            "external_link": "http://example.com"
        }

        response = client.put("/api/insights/1/", data= "not json")
        assert response.status_code in [400, 415]

        response = client.put("/api/insights/100/", json=valid_insight)
        assert response.status_code == 404

        response = client.put("/api/insights/1/", json=valid_insight)
        assert response.status_code == 204

        valid_insight.pop("title")
        response = client.put("/api/insights/1/", json=valid_insight)
        assert response.status_code == 400

    def test_delete(self, client):
        """
        Test delete insight with insight id
        """
        response = client.delete("/api/insights/100/")
        assert response.status_code == 404

        response = client.delete("/api/insights/1/")
        assert response.status_code == 204

        response = client.delete("/api/insights/1/")
        assert response.status_code == 404

class TestInsightCollectionByUserItem():
    """
    Test for all the insights created by a user, a simple list without much detail
    """
    def test_get(self, client):
        """
        Test get insights created by a user
        """
        response = client.get("/api/users/testuser1/insights/")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 2

class TestAllInsights():
    """
    Test for insights to be displayed on the map. No need to be detailed
    """
    def test_get(self, client):
        """
        Test get all insights
        """
        response = client.get("/api/insights/")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 3

class TestInsightItemByUserItem():
    """
    Test for single insight created by a user
    """
    def test_post(self, client):
        """
        Test create insight
        """
        valid_insight = {
            "title": "New Insight",
            "description": "New Description",
            "longitude": 25.473,
            "latitude": 65.012,
            "image": "newimage.jpg",
            "address": "123 Test Street, Oulu",
            "category": "Food & Drink",
            "subcategory": "Cafe",
            "external_link": "http://example.com"
        }

        response = client.post("/api/users/testuser1/insights/", data= "not json")
        assert response.status_code in [400, 415]

        response = client.post("/api/users/testuser1/insights/", json=valid_insight)
        assert response.status_code == 201
        assert response.headers["Location"].endswith("/api/insights/4/")
        response = client.get(response.headers["Location"])
        assert response.status_code == 200

        # response = client.post("/api/users/testuser1/insights/", json=valid_insight)
        # assert response.status_code == 409

        valid_insight.pop("title")
        response = client.post("/api/users/testuser1/insights/", json=valid_insight)
        assert response.status_code == 400
