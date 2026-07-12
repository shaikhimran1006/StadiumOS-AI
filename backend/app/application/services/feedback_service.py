from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from app.domain.entities.feedback import (
    Feedback,
    FeedbackCategory,
    FeedbackSentiment,
    FeedbackSource,
)
from app.domain.interfaces.ai_services import IGenerativeAIService
from app.domain.interfaces.external_services import IBigQueryService, IPubSubService, PubSubMessage
from app.domain.interfaces.repositories import IFeedbackRepository
from app.domain.value_objects.gps_sector import GpsSector

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_FEEDBACK = "feedback_events"

SENTIMENT_PROMPT_TEMPLATE = (
    "Analyze the sentiment of the following stadium feedback comment. "
    "Return a JSON object with keys 'sentiment' (one of VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE) "
    "and 'confidence' (float 0-1).\n\nComment: \"{comment}\"\nRating: {rating}/5"
)


class FeedbackService:
    def __init__(
        self,
        feedback_repo: IFeedbackRepository,
        generative_ai: IGenerativeAIService | None = None,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._feedback = feedback_repo
        self._ai = generative_ai
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def create_feedback(
        self,
        user_id: UUID,
        stadium_id: UUID,
        category: str = "GENERAL",
        rating: int = 3,
        comment: str = "",
        event_id: UUID | None = None,
        sector: GpsSector | None = None,
        anonymous: bool = False,
        conversation_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Feedback:
        try:
            cat = FeedbackCategory(category)
        except ValueError:
            cat = FeedbackCategory.GENERAL

        sentiment = await self.analyze_sentiment(comment, rating)

        feedback = Feedback(
            user_id=user_id,
            stadium_id=stadium_id,
            event_id=event_id,
            category=cat,
            rating=rating,
            comment=comment,
            sentiment=sentiment,
            sector=sector,
            conversation_id=conversation_id,
            tags=tags or [],
            metadata=metadata or {},
            is_anonymous=anonymous,
        )

        created = await self._feedback.create(feedback)
        logger.info(
            "Feedback created: %s (category=%s, rating=%d, sentiment=%s)",
            created.id, cat.value, rating, sentiment.value if sentiment else "None",
        )

        await self._publish_feedback_event(created, "feedback_created")
        await self._log_feedback_event(created, "created")

        return created

    async def get_feedback(self, feedback_id: UUID) -> Feedback | None:
        return await self._feedback.get_by_id(feedback_id)

    async def list_feedback_by_event(
        self,
        event_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Feedback]:
        return await self._feedback.list_by_event(event_id, offset=offset, limit=limit)

    async def list_feedback_by_stadium(
        self,
        stadium_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Feedback]:
        return await self._feedback.list_by_stadium(stadium_id, offset=offset, limit=limit)

    async def list_feedback_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Feedback]:
        return await self._feedback.list_by_user(user_id, offset=offset, limit=limit)

    async def list_feedback_by_category(
        self,
        category: FeedbackCategory,
        stadium_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Feedback]:
        return await self._feedback.list_by_category(
            category, stadium_id=stadium_id, offset=offset, limit=limit
        )

    async def respond_to_feedback(
        self,
        feedback_id: UUID,
        response_text: str,
        responder_id: UUID,
    ) -> Feedback | None:
        feedback = await self._feedback.get_by_id(feedback_id)
        if feedback is None:
            return None

        feedback.respond(response_text, responder_id)
        updated = await self._feedback.update(feedback)
        logger.info("Feedback %s responded to by user %s", feedback_id, responder_id)

        await self._publish_feedback_event(updated, "feedback_responded")
        return updated

    async def upvote_feedback(self, feedback_id: UUID) -> Feedback | None:
        feedback = await self._feedback.get_by_id(feedback_id)
        if feedback is None:
            return None

        feedback.upvote()
        updated = await self._feedback.update(feedback)
        return updated

    async def get_analytics(
        self,
        stadium_id: UUID,
        event_id: UUID | None = None,
    ) -> dict[str, Any]:
        if event_id is not None:
            feedback_list = await self._feedback.list_by_event(event_id, limit=1000)
        else:
            feedback_list = await self._feedback.list_by_stadium(stadium_id, limit=1000)

        if not feedback_list:
            return {
                "total_count": 0,
                "average_rating": 0.0,
                "category_breakdown": {},
                "sentiment_distribution": {},
                "rating_distribution": {},
                "top_negative_categories": [],
                "response_rate": 0.0,
            }

        total_count = len(feedback_list)
        total_rating = sum(f.rating for f in feedback_list)
        average_rating = round(total_rating / total_count, 2) if total_count > 0 else 0.0

        category_breakdown: dict[str, int] = defaultdict(int)
        sentiment_distribution: dict[str, int] = defaultdict(int)
        rating_distribution: dict[str, int] = defaultdict(int)
        category_negative: dict[str, int] = defaultdict(int)
        responded_count = 0

        for f in feedback_list:
            category_breakdown[f.category.value] += 1
            if f.sentiment:
                sentiment_distribution[f.sentiment.value] += 1
            rating_distribution[str(f.rating)] += 1
            if f.is_negative():
                category_negative[f.category.value] += 1
            if f.response is not None:
                responded_count += 1

        top_negative = sorted(
            category_negative.items(), key=lambda x: x[1], reverse=True
        )[:5]

        response_rate = round(responded_count / total_count, 2) if total_count > 0 else 0.0

        return {
            "total_count": total_count,
            "average_rating": average_rating,
            "category_breakdown": dict(category_breakdown),
            "sentiment_distribution": dict(sentiment_distribution),
            "rating_distribution": dict(rating_distribution),
            "top_negative_categories": [
                {"category": cat, "count": cnt} for cat, cnt in top_negative
            ],
            "response_rate": response_rate,
        }

    async def analyze_sentiment(
        self, comment: str, rating: int = 3
    ) -> FeedbackSentiment | None:
        if not comment.strip():
            return self._rating_to_sentiment(rating)

        if self._ai is None:
            return self._rating_to_sentiment(rating)

        try:
            prompt = SENTIMENT_PROMPT_TEMPLATE.format(comment=comment, rating=rating)
            response = await self._ai.generate_response(
                prompt=prompt,
                system_instruction=(
                    "You are a sentiment analysis engine. "
                    "Respond ONLY with a valid JSON object: "
                    '{"sentiment": "SENTIMENT_LABEL", "confidence": 0.0}'
                ),
                temperature=0.1,
                max_tokens=100,
            )
            import json

            parsed = json.loads(response.content)
            sentiment_str = parsed.get("sentiment", "").upper()
            try:
                return FeedbackSentiment(sentiment_str)
            except ValueError:
                return self._rating_to_sentiment(rating)
        except Exception:
            logger.exception("Sentiment analysis failed, falling back to rating-based")
            return self._rating_to_sentiment(rating)

    def _rating_to_sentiment(self, rating: int) -> FeedbackSentiment:
        if rating == 5:
            return FeedbackSentiment.VERY_POSITIVE
        if rating == 4:
            return FeedbackSentiment.POSITIVE
        if rating == 3:
            return FeedbackSentiment.NEUTRAL
        if rating == 2:
            return FeedbackSentiment.NEGATIVE
        return FeedbackSentiment.VERY_NEGATIVE

    async def _publish_feedback_event(self, feedback: Feedback, event_type: str) -> None:
        if self._pubsub is None:
            return
        try:
            message = PubSubMessage(
                topic="stadiumos-analytics",
                data={
                    "event_type": event_type,
                    "feedback_id": str(feedback.id),
                    "user_id": str(feedback.user_id),
                    "stadium_id": str(feedback.stadium_id),
                    "event_id": str(feedback.event_id) if feedback.event_id else None,
                    "category": feedback.category.value,
                    "rating": feedback.rating,
                    "sentiment": feedback.sentiment.value if feedback.sentiment else None,
                    "timestamp": feedback.created_at.isoformat(),
                },
                attributes={
                    "feedback_id": str(feedback.id),
                    "category": feedback.category.value,
                },
            )
            await self._pubsub.publish("stadiumos-analytics", message)
        except Exception:
            logger.exception("Failed to publish feedback event to Pub/Sub")

    async def _log_feedback_event(self, feedback: Feedback, action: str) -> None:
        if self._bigquery is None:
            return
        try:
            row: dict[str, Any] = {
                "feedback_id": str(feedback.id),
                "user_id": str(feedback.user_id) if not feedback.is_anonymous else "anonymous",
                "stadium_id": str(feedback.stadium_id),
                "event_id": str(feedback.event_id) if feedback.event_id else None,
                "category": feedback.category.value,
                "source": feedback.source.value,
                "rating": feedback.rating,
                "sentiment": feedback.sentiment.value if feedback.sentiment else None,
                "has_comment": bool(feedback.comment.strip()),
                "comment_length": len(feedback.comment),
                "sector": feedback.sector.value if feedback.sector else None,
                "action": action,
                "timestamp": feedback.created_at.isoformat(),
            }
            await self._bigquery.insert_rows(BIGQUERY_DATASET, BIGQUERY_TABLE_FEEDBACK, [row])
        except Exception:
            logger.exception("Failed to log feedback event to BigQuery")
