"""Tests for health endpoint."""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check():
    """GET /api/health returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "KrishiRakshak AI"
    assert "version" in data


def test_root_endpoint():
    """GET / returns service status and docs URL."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["docs_url"] == "/docs"
