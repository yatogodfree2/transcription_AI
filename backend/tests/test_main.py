"""Tests for the main FastAPI application."""
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint returns expected response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Smart Assistant API",
        "status": "operational",
        "version": "0.1.0",
    }


def test_health_check():
    """Test the health check endpoint returns expected response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
