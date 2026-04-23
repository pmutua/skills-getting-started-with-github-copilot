import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Snapshot and restore the activities dict to isolate test mutations."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


class TestRootEndpoint:
    def test_root_redirects_to_index(self):
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert expected_location in response.headers["location"]


class TestGetActivities:
    def test_returns_all_activities(self):
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Debate Team",
            "Math Olympiad",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Society",
            "Choir",
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        for name in expected_activities:
            assert name in data

    def test_activity_has_required_fields(self):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        for name, details in data.items():
            for field in required_fields:
                assert field in details, f"Activity '{name}' missing field '{field}'"


class TestSignup:
    def test_signup_success(self):
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities[activity]["participants"]

    def test_signup_activity_not_found(self):
        # Arrange
        activity = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self):
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # already enrolled

        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestUnregister:
    def test_unregister_success(self):
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # existing participant

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in activities[activity]["participants"]

    def test_unregister_activity_not_found(self):
        # Arrange
        activity = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_participant_not_found(self):
        # Arrange
        activity = "Chess Club"
        email = "nobody@mergington.edu"  # not enrolled

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in this activity"
