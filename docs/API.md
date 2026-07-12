# StadiumOS AI - API Reference

**Base URL**: `https://<cloud-run-url>/api/v1`

**Authentication**: Bearer token in `Authorization` header for all endpoints except `/health`, `/ready`, `/live`.

```
Authorization: Bearer <jwt_token>
```

## Rate Limiting

| Tier | Requests/Minute |
|------|-----------------|
| Default | 60 |
| Authenticated | 120 |
| Admin | 300 |

Rate limit headers returned:
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Reset timestamp

---

## Infrastructure Endpoints

### `GET /health`

Health check. No authentication required.

**Response** `200 OK`
```json
{"status": "healthy", "service": "StadiumOS AI"}
```

### `GET /ready`

Readiness probe with dependency checks.

**Response** `200 OK`
```json
{
  "status": "ready|degraded",
  "checks": {
    "firestore": "ok",
    "vertex_ai": "ok",
    "pubsub": "ok"
  },
  "version": "1.0.0",
  "environment": "production"
}
```

### `GET /live`

Liveness probe.

**Response** `200 OK`
```json
{"status": "alive", "service": "StadiumOS AI"}
```

---

## Chat Endpoints

### `POST /api/v1/chat`

Send a message and receive an AI response.

**Request Body**
```json
{
  "message": "Where is my seat?",
  "conversation_id": "uuid (optional)",
  "language": "en",
  "context": {
    "stadium_id": "uuid",
    "event_id": "uuid",
    "sector": "A5"
  },
  "message_type": "TEXT"
}
```

**Response** `201 Created`
```json
{
  "response_text": "Your seat is in section A5, row 12, seat 8. Enter through Gate 2.",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "agent_name": "FanAgent",
  "confidence": 0.92,
  "metadata": {"intent": "seating", "latency_ms": 850},
  "sources": ["stadium_map_v3"],
  "actions": []
}
```

### `GET /api/v1/chat/conversations`

List conversations for the authenticated user.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| offset | int | 0 | Pagination offset |
| limit | int | 20 | Items per page (1-100) |

**Response** `200 OK`
```json
[{
  "conversation_id": "uuid",
  "messages": [...],
  "created_at": "2026-07-10T14:30:00Z",
  "updated_at": "2026-07-10T14:35:00Z",
  "status": "ACTIVE",
  "language": "en",
  "message_count": 4
}]
```

### `GET /api/v1/chat/conversations/{conversation_id}`

Get conversation history with messages.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| offset | int | 0 | Message offset |
| limit | int | 50 | Messages per page |

**Response** `200 OK` | `404 Not Found`

### `DELETE /api/v1/chat/conversations/{conversation_id}`

Close a conversation.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| summary | string | null | Conversation summary |
| satisfaction_score | int | null | Rating 1-5 |

**Response** `200 OK` | `404 Not Found`

---

## Alert Endpoints

### `POST /api/v1/alerts`

Create a new alert.

**Request Body**
```json
{
  "alert_type": "SECURITY|MEDICAL|FIRE|EVACUATION|CROWD_SURGE|WEATHER|INFRASTRUCTURE|LOST_PERSON|SUSPICIOUS_PACKAGE|POWER_OUTAGE|WATER_LEAK|GENERIC",
  "title": "Suspicious package near Gate 3",
  "description": "Unattended black bag reported...",
  "priority": 1,
  "sector": "B7",
  "location": {"latitude": 40.7128, "longitude": -74.006},
  "stadium_id": "uuid",
  "event_id": "uuid (optional)",
  "affected_sectors": ["B7", "B8"],
  "triggered_by_ai": true,
  "ai_confidence": 0.87,
  "metadata": {"source": "ai_vision"}
}
```

**Response** `201 Created`
```json
{
  "id": "uuid",
  "alert_type": "SECURITY",
  "title": "Suspicious package near Gate 3",
  "description": "...",
  "priority": 2,
  "status": "TRIGGERED",
  "sector": "B7",
  "stadium_id": "uuid",
  "escalation_level": 0,
  "created_at": "2026-07-10T14:30:00Z",
  "updated_at": "2026-07-10T14:30:00Z"
}
```

### `GET /api/v1/alerts`

List alerts with optional filters.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| stadium_id | uuid | null | Filter by stadium |
| status | string | null | Filter by status |
| offset | int | 0 | Pagination offset |
| limit | int | 20 | Items per page |

**Response** `200 OK`
```json
{
  "alerts": [...],
  "total_count": 5,
  "page": 1,
  "page_size": 20
}
```

### `GET /api/v1/alerts/{alert_id}`

Get alert by ID. `200 OK` | `404 Not Found`

### `PUT /api/v1/alerts/{alert_id}`

Update alert title/description. `200 OK` | `404 Not Found`

### `POST /api/v1/alerts/{alert_id}/escalate`

Escalate alert to next level. `200 OK` | `404 Not Found`

### `POST /api/v1/alerts/{alert_id}/resolve`

Resolve alert. `200 OK` | `404 Not Found`

### `POST /api/v1/alerts/{alert_id}/acknowledge`

Acknowledge and assign alert. `200 OK` | `404 Not Found`

---

## Incident Endpoints

### `POST /api/v1/incidents`

Create a new incident.

**Request Body**
```json
{
  "category": "MEDICAL_EMERGENCY",
  "title": "Fan collapsed in Section C3",
  "description": "Male fan in his 50s collapsed...",
  "severity": "SERIOUS",
  "stadium_id": "uuid",
  "sector": "C3",
  "location": {"latitude": 40.713, "longitude": -74.0062},
  "people_involved": 1,
  "injuries_reported": 1,
  "tags": ["medical", "priority"]
}
```

**Response** `201 Created`

### `GET /api/v1/incidents`

List incidents. Same query params as alerts.

### `GET /api/v1/incidents/{incident_id}`

Get incident by ID. `200 OK` | `404 Not Found`

### `PUT /api/v1/incidents/{incident_id}`

Update incident. `200 OK` | `404 Not Found`

### `POST /api/v1/incidents/{incident_id}/assign`

Assign responder to incident.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| responder_id | uuid | yes | User ID of responder |
| role | string | yes | Role (security, medical, fire) |

### `POST /api/v1/incidents/{incident_id}/resolve`

Resolve incident. **Query**: `resolution_notes` (optional).

---

## Event Endpoints

### `POST /api/v1/events`

Create a new event.

**Request Body**
```json
{
  "name": "FIFA World Cup 2026 - Group A",
  "event_type": "FOOTBALL_MATCH",
  "stadium_id": "uuid",
  "home_team": "USA",
  "away_team": "England",
  "competition": "FIFA World Cup 2026",
  "expected_attendance": 82000,
  "tags": ["world-cup", "group-stage"]
}
```

**Response** `201 Created`

### `GET /api/v1/events`

List events. **Query**: `stadium_id`, `offset`, `limit`.

### `GET /api/v1/events/live`

Get all live events. No auth required for this read-only endpoint.

### `GET /api/v1/events/{event_id}`

Get event by ID. `200 OK` | `404 Not Found`

### `PUT /api/v1/events/{event_id}`

Update event. `200 OK` | `404 Not Found`

---

## Feedback Endpoints

### `POST /api/v1/feedback`

Submit feedback.

**Request Body**
```json
{
  "category": "FOOD_BEVERAGE",
  "rating": 4,
  "comment": "Great variety at the food court!",
  "stadium_id": "uuid",
  "event_id": "uuid (optional)",
  "sector": "A5",
  "anonymous": false,
  "tags": ["food", "positive"]
}
```

**Response** `201 Created`

### `GET /api/v1/feedback`

List feedback. **Query**: `stadium_id`, `event_id`, `category`, `offset`, `limit`.

### `GET /api/v1/feedback/analytics`

Get feedback analytics. **Query**: `stadium_id` (required), `event_id` (optional).

**Response** `200 OK`
```json
{
  "total_count": 1250,
  "average_rating": 4.2,
  "category_breakdown": {"FOOD_BEVERAGE": 350, "CLEANLINESS": 280},
  "sentiment_distribution": {"POSITIVE": 800, "NEUTRAL": 300, "NEGATIVE": 150},
  "rating_distribution": {"1": 50, "2": 100, "3": 200, "4": 500, "5": 400},
  "response_rate": 0.65
}
```

### `GET /api/v1/feedback/{feedback_id}`

Get feedback by ID. `200 OK` | `404 Not Found`

---

## Dashboard Endpoints

### `GET /api/v1/dashboard/overview`

Get dashboard metrics. **Query**: `stadium_id` (required).

### `GET /api/v1/dashboard/sectors`

Get sector status. **Query**: `stadium_id` (required).

### `GET /api/v1/dashboard/stadium/{stadium_id}`

Get stadium overview.

### `GET /api/v1/dashboard/analytics/{metric}`

Get time series data. **Query**: `stadium_id`, `granularity` (hour/day), `hours_back` (1-168).

---

## Speech Endpoints

### `POST /api/v1/speech/transcribe`

Transcribe audio to text.

**Request Body**
```json
{
  "audio_base64": "<base64-encoded PCM audio>",
  "language": "en-US",
  "sample_rate": 16000
}
```

**Response** `200 OK`
```json
{
  "text": "Where is my seat?",
  "confidence": 0.95,
  "language": "en-US",
  "alternatives": []
}
```

### `POST /api/v1/speech/synthesize`

Synthesize text to audio.

**Request Body**
```json
{
  "text": "Your seat is in section A5",
  "language": "en",
  "speaking_rate": 1.0,
  "pitch": 0.0
}
```

**Response** `200 OK`
```json
{"audio_base64": "<base64>", "content_type": "audio/mp3"}
```

### `POST /api/v1/speech/translate`

Transcribe + translate in one call.

**Request Body**
```json
{
  "audio_base64": "<base64>",
  "source_language": "es",
  "target_language": "en"
}
```

**Response** `200 OK`
```json
{
  "original_text": "Donde esta mi asiento?",
  "translated_text": "Where is my seat?",
  "source_language": "es",
  "target_language": "en"
}
```

---

## Translation Endpoints

### `POST /api/v1/translation/translate`

Translate text.

**Request Body**
```json
{
  "text": "Where is the nearest restroom?",
  "target_language": "es",
  "source_language": "en"
}
```

**Response** `200 OK`
```json
{
  "translated_text": "Donde esta el bano mas cercano?",
  "source_language": "en",
  "target_language": "es",
  "confidence": 0.95
}
```

### `POST /api/v1/translation/detect`

Detect language.

**Request Body**: `{"text": "Bonjour le monde"}`

**Response** `200 OK`: `{"language_code": "fr"}`

### `GET /api/v1/translation/languages`

Get supported languages. Returns `[{language_code, display_name}]`.

---

## Vision Endpoints

### `POST /api/v1/vision/analyze`

Analyze an image.

**Request Body**
```json
{
  "image_base64": "<base64-encoded image>",
  "features": ["LABEL_DETECTION", "OBJECT_LOCALIZATION", "SAFE_SEARCH_DETECTION"]
}
```

**Response** `200 OK`
```json
{
  "labels": [{"description": "crowd", "score": 0.95}],
  "objects": [{"name": "person", "confidence": 0.88}],
  "text_detected": null,
  "safety_labels": []
}
```

### `POST /api/v1/vision/ocr`

Extract text from image.

**Request Body**: `{"image_base64": "<base64>"}`

**Response** `200 OK`: `{"extracted_text": "...", "text_length": 42}`

---

## Maps Endpoints

### `POST /api/v1/maps/geocode`

Convert address to coordinates.

**Request Body**: `{"address": "1 MetLife Stadium Dr, NJ"}`

**Response** `200 OK`
```json
{
  "formatted_address": "1 MetLife Stadium Dr, East Rutherford, NJ 07073",
  "latitude": 40.8135,
  "longitude": -74.0745,
  "place_id": "ChIJ..."
}
```

### `POST /api/v1/maps/directions`

Get directions between two points.

**Request Body**
```json
{
  "origin_lat": 40.7128,
  "origin_lon": -74.006,
  "destination_lat": 40.8135,
  "destination_lon": -74.0745,
  "mode": "walking"
}
```

**Response** `200 OK`
```json
{
  "steps": [...],
  "distance_meters": 15200,
  "duration_seconds": 1200,
  "polyline": "encoded_polyline"
}
```

### `POST /api/v1/maps/places`

Find nearby places.

**Request Body**
```json
{
  "latitude": 40.8135,
  "longitude": -74.0745,
  "place_type": "restaurant",
  "radius_meters": 2000
}
```

### `POST /api/v1/maps/distance`

Distance matrix calculation.

---

## Notification Endpoints

### `POST /api/v1/notifications/send`

Send notification to a user.

**Request Body**
```json
{
  "user_id": "uuid",
  "title": "Seat Upgrade Available",
  "body": "A VIP seat in A1 is now available.",
  "notification_type": "info",
  "priority": "normal"
}
```

### `POST /api/v1/notifications/broadcast`

Emergency broadcast to stadium.

**Request Body**
```json
{
  "stadium_id": "uuid",
  "title": "Evacuation Notice",
  "body": "Please evacuate calmly through Gate 4.",
  "severity": "critical",
  "sectors": ["A1", "A2", "B1"]
}
```

### `POST /api/v1/notifications/sector`

Send alert to specific sector.

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "path": "/api/v1/resource"
  }
}
```

### Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `BAD_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `CONFLICT` | 409 | Resource already exists |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `AI_SERVICE_ERROR` | 502 | AI service unavailable |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
| `HTTP_429` | 429 | Rate limit exceeded |

### Validation Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "path": "/api/v1/chat",
    "details": [
      {
        "field": "body -> message",
        "message": "Field required",
        "type": "missing"
      }
    ]
  }
}
```
