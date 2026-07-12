"""Tests for AlertService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.services.alert_service import AlertService
from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


@pytest.fixture
def mock_alert_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_pubsub():
    return AsyncMock()


@pytest.fixture
def mock_bigquery():
    return AsyncMock()


@pytest.fixture
def alert_service(mock_alert_repo, mock_user_repo, mock_pubsub, mock_bigquery):
    return AlertService(
        alert_repo=mock_alert_repo,
        user_repo=mock_user_repo,
        pubsub=mock_pubsub,
        bigquery=mock_bigquery,
    )


@pytest.mark.asyncio
class TestAlertServiceCreateAlert:
    async def test_create_alert(self, alert_service, mock_alert_repo):
        stadium_id = uuid4()
        mock_alert_repo.create.return_value = Alert(
            alert_type=AlertType.SECURITY,
            priority=Priority.HIGH,
            title="Suspicious package",
            description="Unattended bag near gate",
            stadium_id=stadium_id,
            sector=GpsSector.B7,
        )

        alert = await alert_service.create_alert(
            alert_type="SECURITY",
            title="Suspicious package",
            description="Unattended bag near gate",
            stadium_id=stadium_id,
            priority=Priority.HIGH,
            sector=GpsSector.B7,
        )

        assert alert.alert_type == AlertType.SECURITY
        assert alert.priority == Priority.HIGH
        assert alert.sector == GpsSector.B7

    async def test_create_alert_invalid_type_falls_back_to_generic(
        self, alert_service, mock_alert_repo
    ):
        stadium_id = uuid4()
        mock_alert_repo.create.return_value = Alert(
            alert_type=AlertType.GENERIC,
            title="Test",
            description="Desc",
            stadium_id=stadium_id,
        )

        alert = await alert_service.create_alert(
            alert_type="INVALID_TYPE",
            title="Test",
            description="Desc",
            stadium_id=stadium_id,
        )

        assert alert.alert_type == AlertType.GENERIC

    async def test_create_alert_with_ai_trigger(self, alert_service, mock_alert_repo):
        stadium_id = uuid4()
        mock_alert_repo.create.return_value = Alert(
            alert_type=AlertType.CROWD_SURGE,
            title="Crowd surge",
            description="AI detected crowd surge",
            stadium_id=stadium_id,
            triggered_by_ai=True,
            ai_confidence=0.89,
        )

        alert = await alert_service.create_alert(
            alert_type="CROWD_SURGE",
            title="Crowd surge",
            description="AI detected crowd surge",
            stadium_id=stadium_id,
            triggered_by_ai=True,
            ai_confidence=0.89,
        )

        assert alert.triggered_by_ai is True
        assert alert.ai_confidence == 0.89

    async def test_create_alert_publishes_event(self, alert_service, mock_alert_repo, mock_pubsub):
        stadium_id = uuid4()
        mock_alert_repo.create.return_value = Alert(
            alert_type=AlertType.MEDICAL,
            title="Medical",
            description="Desc",
            stadium_id=stadium_id,
        )

        await alert_service.create_alert(
            alert_type="MEDICAL",
            title="Medical",
            description="Desc",
            stadium_id=stadium_id,
        )

        mock_pubsub.publish.assert_called_once()


@pytest.mark.asyncio
class TestAlertServiceEscalateAlert:
    async def test_escalate_alert(self, alert_service, mock_alert_repo):
        alert = Alert(
            alert_type=AlertType.SECURITY,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            escalation_level=0,
        )
        mock_alert_repo.get_by_id.return_value = alert
        mock_alert_repo.update.return_value = alert

        result = await alert_service.escalate_alert(alert.id, user_id=uuid4())

        assert result is not None
        assert result.escalation_level == 1

    async def test_escalate_nonexistent_alert(self, alert_service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None
        result = await alert_service.escalate_alert(uuid4())
        assert result is None

    async def test_escalate_inactive_alert(self, alert_service, mock_alert_repo):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            status=AlertStatus.RESOLVED,
        )
        mock_alert_repo.get_by_id.return_value = alert

        result = await alert_service.escalate_alert(alert.id)
        assert result is not None
        assert result.status == AlertStatus.RESOLVED


@pytest.mark.asyncio
class TestAlertServiceResolveAlert:
    async def test_resolve_alert(self, alert_service, mock_alert_repo):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        mock_alert_repo.get_by_id.return_value = alert
        mock_alert_repo.update.return_value = alert

        result = await alert_service.resolve_alert(alert.id)

        assert result is not None
        assert result.status == AlertStatus.RESOLVED
        assert result.resolved_at is not None

    async def test_resolve_nonexistent_alert(self, alert_service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None
        result = await alert_service.resolve_alert(uuid4())
        assert result is None


@pytest.mark.asyncio
class TestAlertServiceAcknowledgeAlert:
    async def test_acknowledge_alert(self, alert_service, mock_alert_repo):
        alert = Alert(
            alert_type=AlertType.FIRE,
            title="Fire",
            description="Desc",
            stadium_id=uuid4(),
        )
        mock_alert_repo.get_by_id.return_value = alert
        mock_alert_repo.update.return_value = alert

        user_id = uuid4()
        result = await alert_service.acknowledge_alert(alert.id, user_id)

        assert result is not None
        assert result.status == AlertStatus.ACKNOWLEDGED
        assert result.assigned_to_user_id == user_id


@pytest.mark.asyncio
class TestAlertServiceListActiveAlerts:
    async def test_list_active_alerts(self, alert_service, mock_alert_repo):
        alerts = [
            Alert(
                alert_type=AlertType.SECURITY,
                title="Alert 1",
                description="Desc",
                stadium_id=uuid4(),
            ),
            Alert(
                alert_type=AlertType.MEDICAL,
                title="Alert 2",
                description="Desc",
                stadium_id=uuid4(),
            ),
        ]
        mock_alert_repo.list_active.return_value = alerts

        result = await alert_service.list_active_alerts()
        assert len(result) == 2

    async def test_list_active_alerts_by_stadium(self, alert_service, mock_alert_repo):
        stadium_id = uuid4()
        alerts = [
            Alert(
                alert_type=AlertType.SECURITY,
                title="Alert",
                description="Desc",
                stadium_id=stadium_id,
            ),
        ]
        mock_alert_repo.list_by_stadium.return_value = alerts

        result = await alert_service.list_active_alerts(stadium_id=stadium_id)
        assert len(result) == 1


@pytest.mark.asyncio
class TestAlertServiceCancelAlert:
    async def test_cancel_alert(self, alert_service, mock_alert_repo):
        alert = Alert(
            alert_type=AlertType.WEATHER,
            title="Weather alert",
            description="Storm approaching",
            stadium_id=uuid4(),
        )
        mock_alert_repo.get_by_id.return_value = alert
        mock_alert_repo.update.return_value = alert

        result = await alert_service.cancel_alert(alert.id)
        assert result is not None
        assert result.status == AlertStatus.CANCELLED


@pytest.mark.asyncio
class TestAlertServiceGetActiveAlertCount:
    async def test_get_active_alert_count(self, alert_service, mock_alert_repo):
        mock_alert_repo.count_active.return_value = 5
        count = await alert_service.get_active_alert_count()
        assert count == 5

    async def test_get_active_alert_count_by_stadium(self, alert_service, mock_alert_repo):
        stadium_id = uuid4()
        mock_alert_repo.count_active_by_stadium.return_value = 3
        count = await alert_service.get_active_alert_count(stadium_id=stadium_id)
        assert count == 3
