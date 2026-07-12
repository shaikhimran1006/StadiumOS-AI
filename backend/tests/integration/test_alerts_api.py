"""Integration tests for alerts API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.security.auth import create_access_token


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=uuid4(), role="STAFF")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(test_client):
    return test_client


class TestPostAlerts:
    def test_create_alert_unauthenticated(self, client):
        response = client.post("/api/v1/alerts", json={
            "alert_type": "SECURITY",
            "title": "Test",
            "description": "Desc",
            "stadium_id": str(uuid4()),
        })
        assert response.status_code == 401

    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_create_alert_success(self, mock_get_service, client, auth_headers):
        from datetime import datetime, timezone
        from app.domain.entities.alert import Alert, AlertType
        from app.domain.value_objects.priority import Priority

        mock_service = AsyncMock()
        mock_service.create_alert.return_value = Alert(
            alert_type=AlertType.SECURITY,
            priority=Priority.HIGH,
            title="Suspicious package",
            description="Unattended bag near Gate 3",
            stadium_id=uuid4(),
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/alerts",
            json={
                "alert_type": "SECURITY",
                "title": "Suspicious package",
                "description": "Unattended bag near Gate 3",
                "stadium_id": str(uuid4()),
                "priority": 2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["alert_type"] == "SECURITY"
        assert data["priority"] == 2

    def test_create_alert_missing_required_fields(self, client, auth_headers):
        response = client.post(
            "/api/v1/alerts",
            json={"alert_type": "SECURITY"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetAlerts:
    def test_list_alerts_unauthenticated(self, client):
        response = client.get("/api/v1/alerts")
        assert response.status_code == 401

    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_list_alerts_empty(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        mock_service.list_active_alerts.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["alerts"] == []
        assert data["total_count"] == 0

    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_list_alerts_with_stadium_filter(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        mock_service.list_active_alerts.return_value = []
        mock_get_service.return_value = mock_service

        stadium_id = uuid4()
        response = client.get(
            f"/api/v1/alerts?stadium_id={stadium_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestGetAlertById:
    def test_get_alert_unauthenticated(self, client):
        alert_id = uuid4()
        response = client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 401

    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_get_alert_not_found(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        mock_service.get_alert.return_value = None
        mock_get_service.return_value = mock_service

        alert_id = uuid4()
        response = client.get(
            f"/api/v1/alerts/{alert_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestEscalateAlert:
    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_escalate_alert_success(self, mock_get_service, client, auth_headers):
        from app.domain.entities.alert import Alert, AlertStatus, AlertType
        from app.domain.value_objects.priority import Priority

        mock_service = AsyncMock()
        alert = Alert(
            alert_type=AlertType.SECURITY,
            priority=Priority.HIGH,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            escalation_level=0,
        )
        mock_service.escalate_alert.return_value = alert
        mock_get_service.return_value = mock_service

        alert_id = uuid4()
        response = client.post(
            f"/api/v1/alerts/{alert_id}/escalate",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestResolveAlert:
    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_resolve_alert_success(self, mock_get_service, client, auth_headers):
        from app.domain.entities.alert import Alert, AlertStatus, AlertType

        mock_service = AsyncMock()
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Resolved",
            description="Desc",
            stadium_id=uuid4(),
            status=AlertStatus.RESOLVED,
        )
        mock_service.resolve_alert.return_value = alert
        mock_get_service.return_value = mock_service

        alert_id = uuid4()
        response = client.post(
            f"/api/v1/alerts/{alert_id}/resolve",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_resolve_alert_not_found(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        mock_service.resolve_alert.return_value = None
        mock_get_service.return_value = mock_service

        response = client.post(
            f"/api/v1/alerts/{uuid4()}/resolve",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestAcknowledgeAlert:
    @patch("app.api.v1.routers.alerts.get_alert_service")
    def test_acknowledge_alert_success(self, mock_get_service, client, auth_headers):
        from app.domain.entities.alert import Alert, AlertStatus, AlertType

        mock_service = AsyncMock()
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            status=AlertStatus.ACKNOWLEDGED,
        )
        mock_service.acknowledge_alert.return_value = alert
        mock_get_service.return_value = mock_service

        response = client.post(
            f"/api/v1/alerts/{uuid4()}/acknowledge",
            headers=auth_headers,
        )
        assert response.status_code == 200
