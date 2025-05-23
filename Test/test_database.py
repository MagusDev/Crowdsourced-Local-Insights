"""
This module is used to prepare database for test environment.
"""

from datetime import datetime

from geodata import create_app, db
from geodata.models import User, Insight, Feedback


def create_test_users():
    """
    Create test users
    """
    users = [
        User(
            username="admin1",
            email="admin@test.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
            phone=1234567890,
            status="active",
            role="admin",
        ),
        User(
            username="user1",
            email="user1@test.com",
            password="user123",
            first_name="Regular",
            last_name="User",
            phone=9876543210,
            status="active",
            role="user",
        ),
    ]
    return users


def create_test_insights(user):
    """
    Create test insights
    """
    insights = [
        Insight(
            title="Great Coffee Shop",
            description="Amazing coffee and atmosphere",
            longitude=25.4667,
            latitude=65.0167,
            category="Food & Drink",
            subcategory="Cafe",
            address="123 Coffee Street",
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            creator=user.id,
        ),
        Insight(
            title="Beautiful Park",
            description="Perfect for picnics",
            longitude=25.4700,
            latitude=65.0200,
            category="Recreation",
            subcategory="Parks",
            address="456 Park Avenue",
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            creator=user.id,
        ),
    ]
    return insights


def create_test_feedback(user, insight):
    """
    Create test feedback
    """
    feedback = Feedback(
        user_id=user.id,
        insight_id=insight.id,
        rating=5,
        comment="This place is amazing!",
    )
    return feedback


def test_database():
    """
    Prepare database
    """
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        users = create_test_users()
        for user in users:
            db.session.add(user)
        db.session.commit()

        insights = create_test_insights(users[0])
        for insight in insights:
            db.session.add(insight)
        db.session.commit()

        feedback = create_test_feedback(users[1], insights[0])
        db.session.add(feedback)
        db.session.commit()

        print("\nUsers in database:")
        for user in User.query.all():
            print(f"- {user.username} ({user.role})")

        print("\nInsights in database:")
        for insight in Insight.query.all():
            print(f"- {insight.title} by user {insight.creator}")

        print("\nFeedback in database:")
        for feedback in Feedback.query.all():
            print(
                f"- Rating {feedback.rating} by user "
                f"{feedback.user_id} for insight {feedback.insight_id}"
            )


if __name__ == "__main__":
    test_database()
