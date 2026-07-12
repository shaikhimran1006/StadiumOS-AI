# StadiumOS AI

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-pytest-green)](#testing)
[![GCP](https://img.shields.io/badge/Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com)

**Intelligent Stadium Management Platform with multilingual AI agents, real-time operations, and Google Cloud integration.**

---

## Features

- **8 Specialized AI Agents** — Fan experience, security, medical, transport, operations, accessibility, volunteer, and sustainability
- **Multilingual Support** — 25+ FIFA languages with real-time translation
- **Real-time Chat** — Instant AI-powered responses for stadium visitors
- **Smart Alert System** — AI-detected incidents with automatic escalation
- **Incident Management** — Full lifecycle tracking with responder dispatch
- **Event Management** — Schedules, attendance tracking, and live status
- **Voice & Vision** — Speech-to-text, text-to-speech, image analysis, and OCR
- **Interactive Maps** — Navigation, directions, and nearby place search
- **Operations Dashboard** — Real-time metrics, sector status, and analytics
- **Feedback Collection** — Multi-channel feedback with sentiment analysis
- **Emergency Broadcast** — Targeted or stadium-wide safety notifications

## Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Frontend   │   │  Mobile App  │   │   Kiosk UI   │
│   (React)    │   │  (Flutter)   │   │   (React)    │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       └──────────────────┼───────────────────┘
                          ▼
              ┌───────────────────────┐
              │   FastAPI Backend     │
              │   (Clean Arch.)       │
              └───────────┬───────────┘
                          │
       ┌──────────┬───────┼───────┬──────────┐
       ▼          ▼       ▼       ▼          ▼
  ┌─────────┐ ┌───────┐ ┌─────┐ ┌──────┐ ┌───────┐
  │Firestore│ │Pub/Sub│ │BQ   │ │Vertex│ │  GCS  │
  │         │ │       │ │     │ │AI    │ │       │
  └─────────┘ └───────┘ └─────┘ └──────┘ └───────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 |
| **AI/ML** | Vertex AI (Gemini 2.0 Flash), Custom agents |
| **Database** | Cloud Firestore (NoSQL) |
| **Messaging** | Cloud Pub/Sub |
| **Analytics** | BigQuery |
| **Storage** | Cloud Storage (GCS) |
| **Auth** | JWT + OAuth2 (Identity Platform) |
| **Services** | Translation API, Speech API, Vision API, Maps API |
| **Infrastructure** | Cloud Run, Docker, Terraform |
| **Frontend** | React, TypeScript, Vite |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud SDK (`gcloud`)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/stadiumos-ai.git
cd stadiumos-ai

# Copy environment variables
cp .env.example .env
# Edit .env with your GCP project settings

# Install dependencies
make install

# Start with Docker (includes Firestore + Pub/Sub emulators)
make dev
```

The application will be available at:
- **Backend API**: http://localhost:8000
- **API Docs** (dev only): http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Firestore Emulator**: http://localhost:8180

### Without Docker

```bash
# Start Firestore emulator
gcloud beta emulators firestore --host-port=localhost:8180 start &

# Start Pub/Sub emulator
gcloud beta emulators pubsub --host-port=localhost:8280 start &

# Start backend
make dev-backend
```

## Project Structure

```
stadiumos-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── routers/          # API route handlers
│   │   │   ├── middleware/        # Rate limiter, request tracking
│   │   │   ├── dependencies/      # Dependency injection
│   │   │   └── router.py         # Router aggregation
│   │   ├── ai/
│   │   │   ├── agents/           # 8 specialized AI agents
│   │   │   ├── router/           # Agent intent routing
│   │   │   ├── services/         # Generative AI, RAG services
│   │   │   ├── prompts/          # System prompts
│   │   │   └── tools/            # Function tools
│   │   ├── application/
│   │   │   ├── services/         # Business logic services
│   │   │   ├── dto/              # Request/response DTOs
│   │   │   └── use_cases/        # Use case orchestration
│   │   ├── domain/
│   │   │   ├── entities/         # Domain entities
│   │   │   ├── value_objects/    # Value objects
│   │   │   ├── interfaces/       # Repository & service interfaces
│   │   │   └── models/           # Data models
│   │   ├── infrastructure/
│   │   │   ├── firestore/        # Firestore repositories
│   │   │   ├── pubsub/           # Pub/Sub publisher
│   │   │   ├── bigquery/         # BigQuery client
│   │   │   ├── storage/          # GCS client
│   │   │   └── secret_manager/   # Secret Manager
│   │   ├── services/             # External service adapters
│   │   │   ├── translation/      # Google Translation
│   │   │   ├── speech/           # Google Speech
│   │   │   ├── vision/           # Google Vision
│   │   │   ├── maps/             # Google Maps
│   │   │   └── identity/         # Identity Platform
│   │   ├── core/
│   │   │   ├── config/           # Settings (Pydantic)
│   │   │   ├── security/         # JWT auth
│   │   │   ├── exceptions/       # Exception handlers
│   │   │   └── logging/          # Structured logging
│   │   └── main.py               # FastAPI app entry point
│   ├── tests/
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── ai/                   # AI agent tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── AI_AGENTS.md
│   └── SECURITY.md
├── deploy/
├── scripts/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| `DEBUG` | `false` | Enable debug mode |
| `GCP_PROJECT_ID` | - | Google Cloud project ID |
| `GCP_REGION` | `us-central1` | GCP region |
| `JWT_SECRET_KEY` | - | JWT signing secret (min 32 chars) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `VERTEX_AI_MODEL` | `gemini-2.0-flash-001` | Gemini model |
| `VERTEX_AI_MAX_TOKENS` | `8192` | Max output tokens |
| `VERTEX_AI_TEMPERATURE` | `0.3` | Generation temperature |
| `FIRESTORE_COLLECTION_PREFIX` | `stadiumos` | Collection prefix |
| `PUBSUB_TOPIC_ALERTS` | `stadiumos-alerts` | Alerts topic |
| `PUBSUB_TOPIC_ANALYTICS` | `stadiumos-analytics` | Analytics topic |
| `BIGQUERY_DATASET` | `stadiumos_analytics` | Analytics dataset |
| `GCS_BUCKET_MEDIA` | `stadiumos-media` | Media bucket |
| `CORS_ORIGINS` | `["*"]` | Allowed origins |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default rate limit |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL |

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) — System design, data flows, and scalability
- [API Reference](docs/API.md) — All 45+ endpoints with schemas and examples
- [Deployment Guide](docs/DEPLOYMENT.md) — GCP setup, Docker, Cloud Run, CI/CD
- [AI Agents Guide](docs/AI_AGENTS.md) — Agent capabilities, system prompts, and extension guide
- [Security Documentation](docs/SECURITY.md) — Auth, authorization, encryption, and compliance

## Deployment

### Cloud Run (Production)

```bash
# Set up GCP project
make setup-gcp

# Deploy
make deploy-production
```

### Docker

```bash
make docker-build
make docker-up-d
```

## Testing

```bash
# Run all tests
make test-backend

# Run unit tests only
cd backend && python -m pytest tests/unit/ -v

# Run integration tests
cd backend && python -m pytest tests/integration/ -v

# Run with coverage
cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Code Quality

```bash
# Lint
make lint-backend

# Type check
make typecheck-backend

# Format
make format-backend
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Run the test suite (`make test-backend`)
5. Lint and type-check (`make lint typecheck`)
6. Commit your changes
7. Push to the branch and open a Pull Request

### Development Guidelines

- Follow Clean Architecture: Domain → Application → Infrastructure
- Write tests for all new features
- Use async/await for all I/O operations
- Keep functions small and focused
- Use type hints everywhere
- Follow the existing code style (ruff formatter)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
