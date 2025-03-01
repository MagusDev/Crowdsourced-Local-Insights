import os
import sys
import pytest
import tempfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from geodata import db, create_app
from geodata.models import User, Insight, Feedback



@pytest.fixture
def client():
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
            status="active",
            role="user"
        ),
        User(
            username="testuser2",
            email="testuser2@example.com",
            password=User().hash_password("password123"),
            first_name="Test",
            last_name="User2",
            status="active",
            role="user"
        ),
        User(
            username="admin",
            email="admin@example.com",
            password=User().hash_password("adminpass"),
            first_name="Admin",
            last_name="User",
            status="active",
            role="admin"
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
    return {
        "username": f"extrauser{number}",
        "email": f"extrauser{number}@example.com",
        "password": "password123", 
        "first_name": "Extra",
        "last_name": "User",
        "status": "active",
        "role": "user",
    }


class TestUsersCollection(object):
    RESOURSE_URL = "/api/users/"
    def test_get(self, client):

        response = client.get(self.RESOURSE_URL)
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["items"]) == 3
        usernames = [item["username"] for item in body["items"]]
        assert set(usernames) == {"testuser1", "testuser2", "admin"}

    def test_post(self, client):

        
        response = client.post(self.RESOURSE_URL, data= "not json")
        assert response.status_code in [400, 415]

        response = client.post(self.RESOURSE_URL, json=get_user_json())
        assert response.status_code == 201
        assert response.headers["Location"] == "/api/users/4"
        response = client.get("/api/users/4")
        assert response.status_code == 200
        
        response = client.post(self.RESOURSE_URL, json=get_user_json())
        assert response.status_code == 409

        data = get_user_json(2)
        data.pop("email")
        response = client.post(self.RESOURSE_URL, json=data)
        assert response.status_code == 400
