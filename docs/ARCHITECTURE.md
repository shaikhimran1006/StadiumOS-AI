# StadiumOS AI - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          STADIUMOS AI PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │
│  │   Frontend   │   │  Mobile App  │   │   Kiosk UI   │               │
│  │   (React)    │   │  (Flutter)   │   │   (React)    │               │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘               │
│         │                  │                   │                        │
│         └──────────────────┼───────────────────┘                        │
│                            │ HTTPS / WSS                                │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    API GATEWAY (Cloud Load Balancer)             │   │
│  │                    Rate Limiting · CORS · Auth                   │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                         │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │                  FASTAPI APPLICATION SERVER                     │   │
│  │                                                                 │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │                   API LAYER (v1)                          │  │   │
│  │  │  /chat  /alerts  /incidents  /events  /feedback           │  │   │
│  │  │  /dashboard  /speech  /translation  /vision  /maps       │  │   │
│  │  └───────────────────────────┬───────────────────────────────┘  │   │
│  │                              │                                  │   │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │   │
│  │  │              APPLICATION SERVICES LAYER                   │  │   │
│  │  │  ChatService · AlertService · IncidentService             │  │   │
│  │  │  EventService · FeedbackService · DashboardService        │  │   │
│  │  └───────────────────────────┬───────────────────────────────┘  │   │
│  │                              │                                  │   │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │   │
│  │  │                 DOMAIN / ENTITY LAYER                     │  │   │
│  │  │  User · Conversation · Message · Alert · Incident         │  │   │
│  │  │  Event · Stadium · Feedback · Value Objects               │  │   │
│  │  └───────────────────────────┬───────────────────────────────┘  │   │
│  │                              │                                  │   │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │   │
│  │  │               AI AGENTS LAYER                             │  │   │
│  │  │  AgentRouter → FanAgent · SecurityAgent · MedicalAgent    │  │   │
│  │  │  TransportAgent · OperationsAgent · AccessibilityAgent    │  │   │
│  │  │  VolunteerAgent · SustainabilityAgent                     │  │   │
│  │  └───────────────────────────┬───────────────────────────────┘  │   │
│  │                              │                                  │   │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │   │
│  │  │            INFRASTRUCTURE / EXTERNAL SERVICES             │  │   │
│  │  │  Firestore · Pub/Sub · BigQuery · GCS · Secret Manager    │  │   │
│  │  │  Vertex AI · Cloud Vision · Cloud Speech · Translation    │  │   │
│  │  │  Google Maps · Cloud Logging · Cloud Monitoring           │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Clean Architecture Layers

The backend follows **Clean Architecture** (also known as Hexagonal/Ports & Adapters) with strict dependency rules:

### Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE                      │
│  (Firestore, Pub/Sub, BigQuery, GCS, Vertex AI)     │
│  Implements repository interfaces + external services│
├─────────────────────────────────────────────────────┤
│                   APPLICATION                        │
│  (Use Cases, DTOs, Application Services)             │
│  Orchestrates domain logic + infrastructure calls    │
├─────────────────────────────────────────────────────┤
│                     DOMAIN                           │
│  (Entities, Value Objects, Interfaces/Ports)         │
│  Pure business logic, zero framework dependencies    │
└─────────────────────────────────────────────────────┘

Dependency Rule: Inner layers NEVER import outer layers.
Infrastructure implements Domain interfaces.
Application depends on Domain interfaces (not implementations).
```

### Domain Layer (`app/domain/`)

- **Entities**: Core business objects (User, Conversation, Alert, Incident, etc.)
- **Value Objects**: Immutable typed values (LatLong, Priority, Language, GpsSector)
- **Interfaces (Ports)**: Abstract contracts for repositories and services

### Application Layer (`app/application/`)

- **Services**: Orchestrate domain logic (ChatService, AlertService, etc.)
- **DTOs**: Data transfer objects for API request/response validation
- **Use Cases**: Specific business workflows

### Infrastructure Layer (`app/infrastructure/`)

- **Firestore Repositories**: Implement `I*Repository` interfaces
- **Pub/Sub Publisher**: Implements `IPubSubService`
- **BigQuery Client**: Implements `IBigQueryService`
- **Secret Manager**: Handles secret retrieval

### API Layer (`app/api/`)

- **Routers**: FastAPI route definitions
- **Middleware**: Rate limiting, request tracking, logging
- **Dependencies**: Dependency injection (getters)

## Data Flow Diagrams

### Chat Message Flow

```
User → POST /api/v1/chat
  │
  ├─→ Auth Middleware (JWT verification)
  │
  ├─→ ChatService.send_message()
  │     │
  │     ├─→ Get or create Conversation
  │     │
  │     ├─→ Save User Message to Firestore
  │     │
  │     ├─→ Translate (if non-English) ─→ Translation API
  │     │
  │     ├─→ AgentRouter.route_query()
  │     │     ├─→ Classify intent (keyword matching)
  │     │     └─→ Return agent name
  │     │
  │     ├─→ Agent.process()
  │     │     ├─→ Build prompt with system instructions
  │     │     ├─→ Call Vertex AI Gemini
  │     │     ├─→ Parse response (actions, sources)
  │     │     └─→ Return AgentResponse
  │     │
  │     ├─→ Save AI Message to Firestore
  │     │
  │     ├─→ Log to BigQuery (analytics)
  │     │
  │     ├─→ Publish to Pub/Sub (real-time events)
  │     │
  │     └─→ Return ChatResponse
  │
  └─→ HTTP 201 Response
```

### Alert Lifecycle Flow

```
Trigger ─→ AlertService.create_alert()
              │
              ├─→ Save Alert (TRIGGERED) to Firestore
              ├─→ Publish alert_created to Pub/Sub
              └─→ Log to BigQuery
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
  Acknowledge      Escalate       Resolve
  (ACKNOWLEDGED)   (ESCALATED)    (RESOLVED)
         │              │              │
         └──────────────┼──────────────┘
                        ▼
              Publish event + Log
```

## AI Agent Architecture

```
┌──────────────────────────────────────────────┐
│              AgentRouter                      │
│                                               │
│  1. Receive query                             │
│  2. Score categories (keyword matching)       │
│  3. Apply priority tie-breaking               │
│  4. Route to best agent                       │
├──────────────────────────────────────────────┤
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │            BaseAgent (Abstract)          │ │
│  │  - agent_name (abstract)                │ │
│  │  - system_prompt (abstract)             │ │
│  │  - process() (abstract)                 │ │
│  │  - _build_prompt()                      │ │
│  │  - _call_gemini() (with retry)          │ │
│  │  - _parse_response()                    │ │
│  │  - _compute_confidence()                │ │
│  └─────────────────────────────────────────┘ │
│       │       │       │       │       │      │
│       ▼       ▼       ▼       ▼       ▼      │
│  ┌────────┐┌────────┐┌────────┐┌────────┐   │
│  │  Fan   ││Security││Medical ││Transport│   │
│  │ Agent  ││ Agent  ││ Agent  ││ Agent   │   │
│  └────────┘└────────┘└────────┘└────────┘   │
│       │       │       │       │              │
│       ▼       ▼       ▼       ▼              │
│  ┌────────┐┌────────┐┌────────┐┌────────┐   │
│  │Operatns││Access- ││Volun- ││Sustain-│   │
│  │ Agent  ││ibility ││teer   ││ability │   │
│  └────────┘└────────┘└────────┘└────────┘   │
│                                               │
└──────────────────────────────────────────────┘
                    │
                    ▼
           Vertex AI Gemini
```

### Agent Routing Priority

Queries are scored against keyword dictionaries. Higher-scored categories win.
In case of ties, this priority order is used:

1. Security (life-safety first)
2. Medical (life-safety)
3. Accessibility (inclusion)
4. Operations (facility management)
5. Transport (logistics)
6. Volunteer (coordination)
7. Sustainability (environmental)
8. Fan (general, default fallback)

## Google Cloud Service Integration Map

| Service | Usage | Integration |
|---------|-------|-------------|
| **Vertex AI (Gemini)** | AI text generation, agent responses | `GenerativeModel.generate_content()` |
| **Firestore** | Primary database (NoSQL) | `google-cloud-firestore` client |
| **Cloud Pub/Sub** | Event messaging, real-time alerts | `google-cloud-pubsub` publisher |
| **BigQuery** | Analytics, logging, metrics | `google-cloud-bigquery` client |
| **Cloud Storage (GCS)** | Media files, documents, backups | `google-cloud-storage` client |
| **Cloud Translation** | Multi-language support | `google-cloud-translate` client |
| **Cloud Speech** | Voice-to-text / text-to-voice | `google-cloud-speech` client |
| **Cloud Vision** | Image analysis, OCR, safety | `google-cloud-vision` client |
| **Google Maps** | Directions, geocoding, places | Maps JavaScript/Directions API |
| **Secret Manager** | Secure credential storage | `google-cloud-secret-manager` |
| **Cloud Logging** | Structured application logs | `google-cloud-logging` |
| **Cloud Monitoring** | Metrics, dashboards, alerts | `google-cloud-monitoring` |
| **Cloud Scheduler** | Cron jobs, reports | `google-cloud-scheduler` |

## Security Architecture

```
┌─────────────────────────────────────────────┐
│                 CLIENTS                      │
└────────────────────┬────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────┐
│         RATE LIMITER MIDDLEWARE              │
│    (per-IP, per-user request throttling)     │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│          REQUEST TRACKING MIDDLEWARE         │
│       (X-Request-ID, X-Process-Time)        │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│           JWT AUTHENTICATION                │
│  OAuth2PasswordBearer → TokenPayload         │
│  - Validate signature (HS256)               │
│  - Check expiry                              │
│  - Extract user_id, role, stadium_id        │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│          ROLE-BASED ACCESS CONTROL          │
│  FAN → read-only chat + feedback            │
│  STAFF → alerts + incidents + dashboard     │
│  ADMIN → full access + user management      │
│  SECURITY → security-specific endpoints     │
│  MEDICAL → medical-specific endpoints       │
└─────────────────────────────────────────────┘
```

## Scalability Design

### Horizontal Scaling
- **Cloud Run**: Auto-scales 0 → N instances based on request concurrency
- **Stateless servers**: All state in Firestore (no in-memory session)
- **Connection pooling**: Firestore client handles connection management

### Data Partitioning
- **Firestore collections**: Prefixed with `stadiumos_` for multi-tenancy
- **BigQuery**: Partitioned by timestamp for efficient analytics queries
- **Pub/Sub**: Topic-based separation (alerts, analytics, notifications)

### Performance Optimizations
- **Vertex AI retry logic**: Exponential backoff for transient failures
- **Agent keyword routing**: O(n) keyword matching, no ML inference overhead
- **Response caching**: Settings cached via `@lru_cache`
- **Async I/O**: All database/service calls are async

### High Availability
- **Multi-region Firestore**: Automatic replication
- **Cloud Run**: Multiple instances with health checks
- **Pub/Sub**: At-least-once delivery with dead-letter topics
- **BigQuery**: Streaming inserts for real-time analytics
