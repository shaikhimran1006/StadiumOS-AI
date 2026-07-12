"""Tests for health, readiness, and liveness endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(test_client):
    return test_client


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestLivenessProbe:
    def test_liveness_returns_200(self, client):
        response = client.get("/live")
        assert response.status_code == 200

    def test_liveness_response_body(self, client):
        response = client.get("/live")
        data = response.json()
        assert data["status"] == "alive"
        assert "service" in data


class TestReadinessProbe:
    def test_readiness_returns_200(self, client):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_readiness_response_structure(self, client):
        response = client.get("/ready")
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] in ("ready", "degraded")

    def test_readiness_has_service_checks(self, client):
        response = client.get("/ready")
        data = response.json()
        checks = data["checks"]
        assert "firestore" in checks
        assert "vertex_ai" in checks
        assert "pubsub" in checks
