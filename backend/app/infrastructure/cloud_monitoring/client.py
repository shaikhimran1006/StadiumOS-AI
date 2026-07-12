from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import (
    AlertPolicy,
    NotificationChannel,
    UptimeCheckConfig,
)
from google.cloud.monitoring_v3.types import MetricDescriptor, TimeSeries
from google.protobuf.duration_pb2 import Duration
from google.protobuf.field_mask_pb2 import FieldMask

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

METRIC_PREFIX = "custom.googleapis.com/stadiumos"


class MonitoringService:
    def __init__(self) -> None:
        self._metric_client = monitoring_v3.MetricServiceClient()
        self._alert_client = monitoring_v3.AlertPolicyServiceClient()
        self._uptime_client = monitoring_v3.UptimeCheckServiceClient()
        self._project_name = f"projects/{settings.GCP_PROJECT_ID}"

    async def record_metric(
        self, metric_name: str, value: float,
        metric_kind: str = "GAUGE",
        value_type: str = "DOUBLE",
        labels: dict[str, str] | None = None,
        region: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        series = TimeSeries()
        series.metric.type = f"{METRIC_PREFIX}/{metric_name}"
        if labels:
            series.metric.labels.update(labels)
        if region:
            series.resource.labels["location"] = region
        series.resource.type = "global"
        series.resource.labels["project_id"] = settings.GCP_PROJECT_ID

        point = series.points.add()
        point.interval.end_time.seconds = int(now.timestamp())
        point.interval.end_time.nanos = now.microsecond * 1000

        if value_type == "DOUBLE":
            point.value.double_value = value
        else:
            point.value.int64_value = int(value)

        self._metric_client.create_time_series(
            request={"name": self._project_name, "time_series": [series]}
        )
        logger.debug("Recorded metric %s = %s", metric_name, value)

    async def create_alert_policy(
        self, display_name: str, metric_name: str,
        condition_threshold: float, condition_duration_seconds: int = 300,
        comparison: str = "COMPARISON_GT", aggregation_period_seconds: int = 60,
        notification_channels: list[str] | None = None,
        documentation: str | None = None,
        enabled: bool = True,
    ) -> str:
        alert_policy = AlertPolicy(
            display_name=display_name,
            combiner=AlertPolicy.ConditionCombinerType.AND,
            enabled=enabled,
            documentation=AlertPolicy.Documentation(
                content=documentation or f"Alert: {display_name}",
                mime_type="text/markdown",
            ),
        )

        condition = AlertPolicy.Condition(
            display_name=f"{display_name} condition",
            condition_threshold=AlertPolicy.Condition.MetricThreshold(
                filter=(
                    f'metric.type="{METRIC_PREFIX}/{metric_name}" '
                    f'AND resource.type="global"'
                ),
                comparison=comparison,
                threshold_value=condition_threshold,
                duration=Duration(seconds=condition_duration_seconds),
                aggregations=[
                    AlertPolicy.Condition.MetricThreshold.Aggregation(
                        alignment_period=Duration(seconds=aggregation_period_seconds),
                        per_series_aligner=AlertPolicy.Condition.MetricThreshold.Aggregation.Aligner.ALIGN_MEAN,
                        cross_series_reducer=AlertPolicy.Condition.MetricThreshold.Aggregation.Reducer.REDUCE_MEAN,
                    )
                ],
            ),
        )
        alert_policy.conditions.append(condition)

        if notification_channels:
            alert_policy.notification_channels.extend(notification_channels)

        created = self._alert_client.create_alert_policy(
            request={"name": self._project_name, "alert_policy": alert_policy}
        )
        logger.info("Created alert policy %s (%s)", display_name, created.name)
        return created.name

    async def list_alert_policies(self) -> list[dict[str, Any]]:
        policies = self._alert_client.list_alert_policies(
            request={"name": self._project_name}
        )
        results = []
        for policy in policies:
            results.append({
                "name": policy.name,
                "display_name": policy.display_name,
                "enabled": policy.enabled,
                "combiner": str(policy.combiner),
                "conditions": [
                    {
                        "display_name": c.display_name,
                        "condition_type": c.WhichOneof("condition"),
                    }
                    for c in policy.conditions
                ],
                "documentation": policy.documentation.content if policy.documentation else None,
                "creation_record": policy.creation_record.record_time.isoformat()
                if policy.creation_record and policy.creation_record.record_time else None,
            })
        return results

    async def get_uptime_check(self, check_id: str) -> dict[str, Any] | None:
        name = f"{self._project_name}/uptimeCheckConfigs/{check_id}"
        try:
            config = self._uptime_client.get_uptime_check_config(request={"name": name})
            uptime_ip = list(config.selected_regions) if config.selected_regions else []
            return {
                "name": config.name,
                "display_name": config.display_name,
                "period_seconds": config.period.seconds if config.period else None,
                "timeout_seconds": config.timeout.seconds if config.timeout else None,
                "http_check_path": config.http_check.path if config.http_check else None,
                "selected_regions": uptime_ip,
                "is_internal": config.is_internal,
            }
        except Exception as exc:
            logger.warning("Uptime check %s not found: %s", check_id, exc)
            return None

    async def list_uptime_checks(self) -> list[dict[str, Any]]:
        configs = self._uptime_client.list_uptime_check_configs(
            request={"parent": self._project_name}
        )
        results = []
        for config in configs:
            results.append({
                "name": config.name,
                "display_name": config.display_name,
                "period": config.period.seconds if config.period else None,
                "timeout": config.timeout.seconds if config.timeout else None,
                "http_check_path": config.http_check.path if config.http_check else None,
                "is_internal": config.is_internal,
            })
        return results

    async def delete_alert_policy(self, policy_name: str) -> bool:
        try:
            self._alert_client.delete_alert_policy(request={"name": policy_name})
            logger.info("Deleted alert policy %s", policy_name)
            return True
        except Exception as exc:
            logger.error("Failed to delete alert policy %s: %s", policy_name, exc)
            return False
