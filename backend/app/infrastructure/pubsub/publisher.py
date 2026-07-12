from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import PubsubMessage

from app.core.config.settings import settings
from app.domain.interfaces.external_services import IPubSubService, PubSubMessage

logger = logging.getLogger(__name__)

TOPIC_MAP = {
    "alerts": settings.PUBSUB_TOPIC_ALERTS,
    "analytics": settings.PUBSUB_TOPIC_ANALYTICS,
    "notifications": settings.PUBSUB_TOPIC_NOTIFICATIONS,
}

SUBSCRIPTION_MAP = {
    "alerts": settings.PUBSUB_SUBSCRIPTION_ALERTS,
}


class PubSubPublisherService(IPubSubService):
    def __init__(self) -> None:
        self._publisher = pubsub_v1.PublisherClient()
        self._subscriber = pubsub_v1.SubscriberClient()
        self._project_path = f"projects/{settings.GCP_PROJECT_ID}"

    def _resolve_topic_path(self, topic: str) -> str:
        if topic in TOPIC_MAP:
            topic = TOPIC_MAP[topic]
        return self._publisher.topic_path(settings.GCP_PROJECT_ID, topic)

    def _resolve_subscription_path(self, subscription_id: str) -> str:
        return self._subscriber.subscription_path(settings.GCP_PROJECT_ID, subscription_id)

    async def publish(self, topic: str, message: PubSubMessage) -> str:
        topic_path = self._resolve_topic_path(topic)
        data = json.dumps(message.data).encode("utf-8")
        attrs = message.attributes or {}
        future = self._publisher.publish(topic_path, data, **attrs)
        message_id = future.result()
        logger.info("Published message %s to %s", message_id, topic_path)
        return message_id

    async def subscribe(
        self, topic: str, callback: Any, subscription_id: str | None = None,
    ) -> str:
        topic_path = self._resolve_topic_path(topic)
        sub_id = subscription_id or f"sub-{uuid4().hex[:8]}"
        subscription_path = self._subscriber.subscription_path(
            settings.GCP_PROJECT_ID, sub_id
        )
        try:
            self._subscriber.create_subscription(
                name=subscription_path, topic=topic_path
            )
        except Exception:
            logger.warning("Subscription %s already exists", subscription_path)

        future = self._subscriber.subscribe(subscription_path, callback)
        logger.info("Subscribed to %s via %s", topic_path, subscription_path)
        return subscription_path

    async def unsubscribe(self, subscription_id: str) -> bool:
        sub_path = self._resolve_subscription_path(subscription_id)
        try:
            self._subscriber.delete_subscription(subscription=sub_path)
            logger.info("Deleted subscription %s", sub_path)
            return True
        except Exception as exc:
            logger.error("Failed to delete subscription %s: %s", sub_path, exc)
            return False

    async def publish_batch(self, topic: str, messages: list[PubSubMessage]) -> list[str]:
        topic_path = self._resolve_topic_path(topic)
        message_ids: list[str] = []
        publish_futures = []
        for msg in messages:
            data = json.dumps(msg.data).encode("utf-8")
            attrs = msg.attributes or {}
            future = self._publisher.publish(topic_path, data, **attrs)
            publish_futures.append(future)
        for future in publish_futures:
            message_ids.append(future.result())
        logger.info("Published %d messages to %s", len(message_ids), topic_path)
        return message_ids

    async def get_topic_stats(self, topic: str) -> dict[str, Any]:
        topic_path = self._resolve_topic_path(topic)
        try:
            topic_obj = self._publisher.get_topic(topic=topic_path)
            subscriptions = list(self._subscriber.list_subscriptions(
                project=self._project_path
            ))
            sub_count = 0
            for sub in subscriptions:
                if sub.topic == topic_path:
                    sub_count += 1
            return {
                "topic": topic,
                "topic_path": topic_path,
                "labels": dict(topic_obj.labels) if topic_obj.labels else {},
                "subscription_count": sub_count,
            }
        except Exception as exc:
            logger.error("Failed to get topic stats for %s: %s", topic, exc)
            return {"topic": topic, "error": str(exc)}

    async def publish_alert(
        self, alert_id: str, alert_type: str, title: str,
        description: str, priority: str, stadium_id: str,
        **kwargs: Any,
    ) -> str:
        message = PubSubMessage(
            topic=TOPIC_MAP.get("alerts", settings.PUBSUB_TOPIC_ALERTS),
            data={
                "alert_id": alert_id,
                "alert_type": alert_type,
                "title": title,
                "description": description,
                "priority": priority,
                "stadium_id": stadium_id,
                **kwargs,
            },
            attributes={"type": "alert", "alert_type": alert_type, "priority": priority},
        )
        return await self.publish("alerts", message)

    async def publish_analytics(self, event_type: str, payload: dict[str, Any]) -> str:
        message = PubSubMessage(
            topic=TOPIC_MAP.get("analytics", settings.PUBSUB_TOPIC_ANALYTICS),
            data={"event_type": event_type, "payload": payload},
            attributes={"type": "analytics", "event_type": event_type},
        )
        return await self.publish("analytics", message)

    async def publish_notification(
        self, user_id: str, title: str, body: str,
        notification_type: str = "general", **kwargs: Any,
    ) -> str:
        message = PubSubMessage(
            topic=TOPIC_MAP.get("notifications", settings.PUBSUB_TOPIC_NOTIFICATIONS),
            data={
                "user_id": user_id,
                "title": title,
                "body": body,
                "notification_type": notification_type,
                **kwargs,
            },
            attributes={"type": "notification", "notification_type": notification_type},
        )
        return await self.publish("notifications", message)

    async def create_subscription(self, topic: str, subscription_name: str) -> str:
        topic_path = self._resolve_topic_path(topic)
        sub_path = self._subscriber.subscription_path(
            settings.GCP_PROJECT_ID, subscription_name
        )
        try:
            self._subscriber.create_subscription(
                name=sub_path, topic=topic_path,
            )
            logger.info("Created subscription %s for %s", sub_path, topic_path)
        except Exception as exc:
            logger.warning("Subscription creation %s: %s", sub_path, exc)
        return sub_path

    async def acknowledge_message(self, subscription_id: str, ack_ids: list[str]) -> None:
        sub_path = self._resolve_subscription_path(subscription_id)
        subscriber = pubsub_v1.SubscriberClient()
        for ack_id in ack_ids:
            subscriber.acknowledge(subscription=sub_path, ack_ids=[ack_id])
        logger.info("Acknowledged %d messages on %s", len(ack_ids), sub_path)
