"""Tests for health check endpoints."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check():
    """Test the basic health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Status might be "healthy" or "degraded" depending on database connectivity
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int | float)
    assert data["uptime_seconds"] >= 0
    assert "database_status" in data
    assert "database_type" in data
    assert data["database_type"] in ["sqlite", "postgresql", "unknown"]
    assert "dependencies" in data


def test_readiness_check():
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()

    assert "ready" in data
    assert isinstance(data["ready"], bool)
    assert "checks" in data
    assert isinstance(data["checks"], dict)
    assert "timestamp" in data


def test_liveness_check():
    """Test the liveness check endpoint."""
    response = client.get("/health/live")

    assert response.status_code == 200
    data = response.json()

    assert data["alive"] is True
    assert "timestamp" in data


def test_api_docs_accessible():
    """Test that API documentation is accessible in development."""
    response = client.get("/docs")
    # Should be accessible since we're in development mode
    assert response.status_code == 200
