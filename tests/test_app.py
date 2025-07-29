"""
Tests for the Cafe24 POS application
"""
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_app_creation():
    """Test app creation."""
    app = create_app("testing")
    assert app is not None
    assert app.config["TESTING"] is True
