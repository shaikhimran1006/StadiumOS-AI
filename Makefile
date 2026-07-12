# ============================================================================
# StadiumOS AI - Makefile
# ============================================================================

# Configuration
PYTHON          ?= python3
NODE            ?= node
NPM             ?= npm
PIP             ?= pip
GCP_PROJECT     ?= stadiumos-ai-dev
GCP_REGION      ?= us-central1
ENVIRONMENT     ?= development
DOCKER_COMPOSE  ?= docker compose
BACKEND_DIR     := backend
FRONTEND_DIR    := frontend

.PHONY: help install dev build test lint typecheck \
        docker-build docker-up docker-down docker-logs \
        deploy-staging deploy-production \
        seed-data setup-gcp clean format \
        install-backend install-frontend \
        dev-backend dev-frontend

# ============================================================================
# Default
# ============================================================================

help: ## Show this help message
	@echo "StadiumOS AI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Installation
# ============================================================================

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python backend dependencies
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "Backend dependencies installed."

install-frontend: ## Install Node.js frontend dependencies
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && $(NPM) ci
	@echo "Frontend dependencies installed."

# ============================================================================
# Development
# ============================================================================

dev: ## Start full development environment with Docker
	$(DOCKER_COMPOSE) --env-file .env up --build

dev-backend: ## Start only backend development server
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

dev-frontend: ## Start only frontend development server
	cd $(FRONTEND_DIR) && $(NPM) run dev

dev-docker: ## Start dev environment in detached mode
	$(DOCKER_COMPOSE) --env-file .env up --build -d

# ============================================================================
# Build
# ============================================================================

build: build-frontend ## Build all production artifacts

build-backend: ## Build backend Docker image
	docker build -t stadiumos-backend:latest -f $(BACKEND_DIR)/Dockerfile .

build-frontend: ## Build frontend for production
	cd $(FRONTEND_DIR) && NODE_ENV=production $(NPM) run build

# ============================================================================
# Testing
# ============================================================================

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd $(FRONTEND_DIR) && $(NPM) run test -- --run

test-integration: ## Run integration tests
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/integration/ -v --tb=long

test-e2e: ## Run end-to-end tests
	cd $(FRONTEND_DIR) && $(NPM) run test:e2e

# ============================================================================
# Code Quality
# ============================================================================

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run Python linters (ruff)
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check . --fix
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff format .

lint-frontend: ## Run frontend linters
	cd $(FRONTEND_DIR) && $(NPM) run lint

typecheck: typecheck-backend typecheck-frontend ## Run all type checks

typecheck-backend: ## Run Python type checks (mypy)
	cd $(BACKEND_DIR) && $(PYTHON) -m mypy app/ --ignore-missing-imports

typecheck-frontend: ## Run TypeScript type checks
	cd $(FRONTEND_DIR) && $(NPM) run typecheck

format: format-backend format-frontend ## Format all code

format-backend: ## Format Python code
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff format .
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check . --fix

format-frontend: ## Format frontend code
	cd $(FRONTEND_DIR) && $(NPM) run format
	cd $(FRONTEND_DIR) && $(NPM) run lint -- --fix

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

docker-build-backend: ## Build backend Docker image only
	$(DOCKER_COMPOSE) build backend

docker-build-frontend: ## Build frontend Docker image only
	$(DOCKER_COMPOSE) build frontend

docker-up: ## Start all services
	$(DOCKER_COMPOSE) --env-file .env up

docker-up-d: ## Start all services (detached)
	$(DOCKER_COMPOSE) --env-file .env up -d

docker-down: ## Stop all services
	$(DOCKER_COMPOSE) down

docker-down-clean: ## Stop all services and remove volumes
	$(DOCKER_COMPOSE) down -v --remove-orphans

docker-logs: ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f

docker-logs-backend: ## Tail backend logs
	$(DOCKER_COMPOSE) logs -f backend

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

docker-restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

# ============================================================================
# Deployment
# ============================================================================

deploy-staging: ## Deploy to staging environment
	GCP_PROJECT_ID=$(GCP_PROJECT) ENVIRONMENT=staging ./scripts/deploy.sh staging

deploy-production: ## Deploy to production environment
	@echo "Deploying to production..."
	GCP_PROJECT_ID=$(GCP_PROJECT) ENVIRONMENT=production ./scripts/deploy.sh production

deploy-status: ## Show deployment status
	@echo "Backend:"
	@gcloud run services describe stadiumos-backend --region=$(GCP_REGION) --format="table(status.url,status.latestReadyRevisionName,status.conditions[0].status)" 2>/dev/null || echo "Not deployed"
	@echo ""
	@echo "Frontend:"
	@gcloud run services describe stadiumos-frontend --region=$(GCP_REGION) --format="table(status.url,status.latestReadyRevisionName,status.conditions[0].status)" 2>/dev/null || echo "Not deployed"

# ============================================================================
# GCP Setup
# ============================================================================

setup-gcp: ## Set up GCP project resources
	./scripts/setup-gcp.sh $(GCP_PROJECT) $(GCP_REGION)

setup-gcp-staging: ## Set up GCP staging environment
	./scripts/setup-gcp.sh stadiumos-ai-staging $(GCP_REGION)

setup-gcp-prod: ## Set up GCP production environment
	./scripts/setup-gcp.sh stadiumos-ai-prod $(GCP_REGION)

seed-data: ## Seed Firestore with development data
	ENVIRONMENT=$(ENVIRONMENT) GCP_PROJECT_ID=$(GCP_PROJECT) ./scripts/seed-data.sh $(ENVIRONMENT)

# ============================================================================
# Firestore
# ============================================================================

firestore-deploy-rules: ## Deploy Firestore security rules
	firebase deploy --only firestore:rules --project $(GCP_PROJECT)

firestore-deploy-indexes: ## Deploy Firestore indexes
	firebase deploy --only firestore:indexes --project $(GCP_PROJECT)

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean build artifacts and caches
	@echo "Cleaning build artifacts..."
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/build $(FRONTEND_DIR)/.next
	rm -rf $(BACKEND_DIR)/dist $(BACKEND_DIR)/build $(BACKEND_DIR)/.mypy_cache
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.ruff_cache
	rm -rf $(BACKEND_DIR)/htmlcov $(BACKEND_DIR)/.coverage
	rm -rf $(FRONTEND_DIR)/node_modules/.cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."

clean-docker: ## Remove all Docker containers, images, and volumes for this project
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi local
	docker system prune -f

clean-all: clean clean-docker ## Clean everything

# ============================================================================
# Utilities
# ============================================================================

logs-cloud: ## View Cloud Run backend logs
	gcloud logging read 'resource.labels.service_name="stadiumos-backend"' \
		--limit=50 --project=$(GCP_PROJECT) --format="table(timestamp,textPayload)"

logs-cloud-frontend: ## View Cloud Run frontend logs
	gcloud logging read 'resource.labels.service_name="stadiumos-frontend"' \
		--limit=50 --project=$(GCP_PROJECT) --format="table(timestamp,textPayload)"

shell-backend: ## Open a shell in the running backend container
	docker exec -it stadiumos-backend /bin/bash

shell-frontend: ## Open a shell in the running frontend container
	docker exec -it stadiumos-frontend /bin/sh

migrate: ## Run database migrations
	cd $(BACKEND_DIR) && $(PYTHON) -m alembic upgrade head

generate-secret: ## Generate a random secret key
	@python3 -c "import secrets; print(secrets.token_urlsafe(64))"
