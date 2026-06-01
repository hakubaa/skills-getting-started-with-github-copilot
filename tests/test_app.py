import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Snapshot of the original activities state for test isolation
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory database before each test."""
    yield
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


@pytest.fixture
def client():
    return TestClient(app)


# --- GET / ---

def test_root_redirects_to_index(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# --- GET /activities ---

def test_get_activities_returns_all(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_get_activities_structure(client):
    response = client.get("/activities")
    data = response.json()
    for name, info in data.items():
        assert "description" in info
        assert "schedule" in info
        assert "max_participants" in info
        assert "participants" in info


# --- POST /activities/{name}/signup ---

def test_signup_success(client):
    response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    # Verify participant was actually added
    act_response = client.get("/activities")
    assert "newstudent@mergington.edu" in act_response.json()["Chess Club"]["participants"]


def test_signup_duplicate_email(client):
    # michael@mergington.edu is already in Chess Club
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_activity_not_found(client):
    response = client.post("/activities/Nonexistent Club/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


# --- DELETE /activities/{name}/unregister ---

def test_unregister_success(client):
    # michael@mergington.edu is in Chess Club
    response = client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    # Verify participant was actually removed
    act_response = client.get("/activities")
    assert "michael@mergington.edu" not in act_response.json()["Chess Club"]["participants"]


def test_unregister_not_enrolled(client):
    response = client.delete("/activities/Chess Club/unregister?email=nobody@mergington.edu")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_unregister_activity_not_found(client):
    response = client.delete("/activities/Nonexistent Club/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]
