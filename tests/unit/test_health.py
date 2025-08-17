import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_health_detailed():
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
