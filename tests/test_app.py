"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def sample_activities():
    """Get the expected activities data structure"""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Compete in basketball leagues and tournaments",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in matches",
            "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
            "max_participants": 10,
            "participants": ["jordan@mergington.edu", "casey@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["maya@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in plays and theatrical productions",
            "schedule": "Wednesdays and Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["alex@mergington.edu", "taylor@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["ryan@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore STEM topics",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 22,
            "participants": ["nina@mergington.edu", "kevin@mergington.edu"]
        }
    }


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/")
        assert response.status_code == 307  # Temporary Redirect
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Test the activities endpoint"""

    def test_get_activities_success(self, client, sample_activities):
        """Test getting all activities returns correct data"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All 9 activities

        # Check that all expected activities are present
        for activity_name in sample_activities.keys():
            assert activity_name in data
            assert "description" in data[activity_name]
            assert "schedule" in data[activity_name]
            assert "max_participants" in data[activity_name]
            assert "participants" in data[activity_name]
            assert isinstance(data[activity_name]["participants"], list)

    def test_get_activities_structure_matches_sample(self, client, sample_activities):
        """Test that returned activities match expected structure"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, expected_data in sample_activities.items():
            assert data[activity_name] == expected_data


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        email = "test@mergington.edu"
        activity = "Chess Club"

        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert f"Signed up {email} for {activity}" in data["message"]

        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]

    def test_signup_duplicate_prevention(self, client):
        """Test that duplicate signup is prevented"""
        email = "duplicate@mergington.edu"
        activity = "Programming Class"

        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400

        data = response2.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        email = "test@mergington.edu"
        activity = "NonExistent Activity"

        response = client.delete(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 405  # Method not allowed for DELETE

        # Use POST instead
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_empty_email(self, client):
        """Test signup with empty email"""
        activity = "Gym Class"

        response = client.post(f"/activities/{activity}/signup?email=")
        assert response.status_code == 200  # FastAPI handles empty strings

        # But let's test with a more realistic empty case
        response = client.post(f"/activities/{activity}/signup")
        assert response.status_code == 422  # Validation error for missing required param


class TestRemoveParticipantEndpoint:
    """Test the remove participant endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        email = "test_remove@mergington.edu"
        activity = "Tennis Club"

        # First add the participant
        client.post(f"/activities/{activity}/signup?email={email}")

        # Now remove them
        response = client.delete(f"/activities/{activity}/participants?email={email}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert f"Removed {email} from {activity}" in data["message"]

        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_remove_nonexistent_participant(self, client):
        """Test removing a participant who is not signed up"""
        email = "not_signed_up@mergington.edu"
        activity = "Art Studio"

        response = client.delete(f"/activities/{activity}/participants?email={email}")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]

    def test_remove_from_nonexistent_activity(self, client):
        """Test removing from non-existent activity"""
        email = "test@mergington.edu"
        activity = "Fake Activity"

        response = client.delete(f"/activities/{activity}/participants?email={email}")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_remove_participant_empty_email(self, client):
        """Test removing with empty email"""
        activity = "Debate Team"

        response = client.delete(f"/activities/{activity}/participants?email=")
        assert response.status_code == 404  # Empty string is not a participant

        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]

        # Test missing email parameter
        response = client.delete(f"/activities/{activity}/participants")
        assert response.status_code == 422  # Validation error