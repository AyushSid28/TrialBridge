"""HTTP smoke tests that do not need a live database."""

from fastapi.testclient import TestClient

from src.main import app


def test_root_identifies_trialbridge() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "TrialBridge"
    assert body["docs"] == "/docs"
    assert body["health"] == "/health"


def test_health_reports_app_version() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["name"] == "TrialBridge"
    assert "version" in body
