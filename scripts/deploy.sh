#!/usr/bin/env bash
# ============================================================================
# StadiumOS AI - Deployment Script
# Builds, pushes, and deploys to Cloud Run
# Usage: ./scripts/deploy.sh [staging|production]
# ============================================================================
set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
ENVIRONMENT="${1:-staging}"
PROJECT_ID="${GCP_PROJECT_ID:-stadiumos-ai-${ENVIRONMENT}}"
REGION="${GCP_REGION:-us-central1}"
REPOSITORY="stadiumos"
COMMIT_SHA="${GITHUB_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')}"
BACKEND_SERVICE="stadiumos-backend"
FRONTEND_SERVICE="stadiumos-frontend"
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/backend:${COMMIT_SHA}"
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/frontend:${COMMIT_SHA}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

step() { echo -e "\n${GREEN}==>${NC} $1"; }

# ============================================================================
# Pre-flight checks
# ============================================================================
step "Verifying deployment prerequisites"

if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found"
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not found"
fi

if [ ! -f "backend/Dockerfile" ]; then
    log_error "backend/Dockerfile not found. Run from project root."
fi

if [ ! -f "frontend/Dockerfile" ]; then
    log_error "frontend/Dockerfile not found. Run from project root."
fi

gcloud config set project "${PROJECT_ID}" 2>/dev/null
log_ok "Project: ${PROJECT_ID}"
log_ok "Environment: ${ENVIRONMENT}"
log_ok "Commit SHA: ${COMMIT_SHA}"

# ============================================================================
# Step 1: Build Backend Image
# ============================================================================
step "Building backend image"

docker build \
    --cache-from "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/backend:latest" \
    -t "${BACKEND_IMAGE}" \
    -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/backend:latest" \
    -f backend/Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

log_ok "Backend image built: ${BACKEND_IMAGE}"

# ============================================================================
# Step 2: Build Frontend Image
# ============================================================================
step "Building frontend image"

docker build \
    --cache-from "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/frontend:latest" \
    -t "${FRONTEND_IMAGE}" \
    -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/frontend:latest" \
    -f frontend/Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --build-arg NODE_ENV=production \
    .

log_ok "Frontend image built: ${FRONTEND_IMAGE}"

# ============================================================================
# Step 3: Push Images to Artifact Registry
# ============================================================================
step "Pushing images to Artifact Registry"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet 2>/dev/null

docker push "${BACKEND_IMAGE}"
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/backend:latest"
log_ok "Backend image pushed"

docker push "${FRONTEND_IMAGE}"
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/frontend:latest"
log_ok "Frontend image pushed"

# ============================================================================
# Step 4: Deploy Backend to Cloud Run
# ============================================================================
step "Deploying backend to Cloud Run"

BACKEND_ENV_VARS="ENVIRONMENT=${ENVIRONMENT},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},PORT=8080,LOG_LEVEL=info"

if [ "${ENVIRONMENT}" = "production" ]; then
    BACKEND_MEMORY="2Gi"
    BACKEND_CPU="2"
    BACKEND_MIN_INSTANCES="1"
    BACKEND_MAX_INSTANCES="20"
    BACKEND_CONCURRENCY="80"
    BACKEND_TIMEOUT="300"
else
    BACKEND_MEMORY="1Gi"
    BACKEND_CPU="1"
    BACKEND_MIN_INSTANCES="0"
    BACKEND_MAX_INSTANCES="5"
    BACKEND_CONCURRENCY="40"
    BACKEND_TIMEOUT="120"
fi

gcloud run deploy "${BACKEND_SERVICE}" \
    --image="${BACKEND_IMAGE}" \
    --region="${REGION}" \
    --platform=managed \
    --service-account="${BACKEND_SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --memory="${BACKEND_MEMORY}" \
    --cpu="${BACKEND_CPU}" \
    --min-instances="${BACKEND_MIN_INSTANCES}" \
    --max-instances="${BACKEND_MAX_INSTANCES}" \
    --concurrency="${BACKEND_CONCURRENCY}" \
    --timeout="${BACKEND_TIMEOUT}" \
    --set-env-vars="${BACKEND_ENV_VARS}" \
    --allow-unauthenticated \
    --no-use-http2 \
    --quiet

BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" \
    --region="${REGION}" \
    --format="value(status.url)")

log_ok "Backend deployed: ${BACKEND_URL}"

# ============================================================================
# Step 5: Deploy Frontend to Cloud Run
# ============================================================================
step "Deploying frontend to Cloud Run"

FRONTEND_ENV_VARS="ENVIRONMENT=${ENVIRONMENT},PORT=80,BACKEND_URL=${BACKEND_URL}"

if [ "${ENVIRONMENT}" = "production" ]; then
    FRONTEND_MEMORY="256Mi"
    FRONTEND_CPU="1"
    FRONTEND_MIN_INSTANCES="1"
    FRONTEND_MAX_INSTANCES="10"
    FRONTEND_CONCURRENCY="80"
    FRONTEND_TIMEOUT="60"
else
    FRONTEND_MEMORY="128Mi"
    FRONTEND_CPU="1"
    FRONTEND_MIN_INSTANCES="0"
    FRONTEND_MAX_INSTANCES="3"
    FRONTEND_CONCURRENCY="40"
    FRONTEND_TIMEOUT="30"
fi

gcloud run deploy "${FRONTEND_SERVICE}" \
    --image="${FRONTEND_IMAGE}" \
    --region="${REGION}" \
    --platform=managed \
    --service-account="${FRONTEND_SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --memory="${FRONTEND_MEMORY}" \
    --cpu="${FRONTEND_CPU}" \
    --min-instances="${FRONTEND_MIN_INSTANCES}" \
    --max-instances="${FRONTEND_MAX_INSTANCES}" \
    --concurrency="${FRONTEND_CONCURRENCY}" \
    --timeout="${FRONTEND_TIMEOUT}" \
    --set-env-vars="${FRONTEND_ENV_VARS}" \
    --allow-unauthenticated \
    --no-use-http2 \
    --quiet

FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" \
    --region="${REGION}" \
    --format="value(status.url)")

log_ok "Frontend deployed: ${FRONTEND_URL}"

# ============================================================================
# Step 6: Verify Deployment
# ============================================================================
step "Verifying deployment"

sleep 10

BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo "000")
if [ "${BACKEND_HEALTH}" = "200" ]; then
    log_ok "Backend health check: PASS"
else
    log_warn "Backend health check returned: ${BACKEND_HEALTH} (may need a moment to start)"
fi

FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/health" 2>/dev/null || echo "000")
if [ "${FRONTEND_HEALTH}" = "200" ]; then
    log_ok "Frontend health check: PASS"
else
    log_warn "Frontend health check returned: ${FRONTEND_HEALTH} (may need a moment to start)"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN} StadiumOS AI - Deployment Complete (${ENVIRONMENT})${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e " Backend:   ${BLUE}${BACKEND_URL}${NC}"
echo -e " Frontend:  ${BLUE}${FRONTEND_URL}${NC}"
echo -e " Image:     ${BLUE}${COMMIT_SHA}${NC}"
echo ""
echo -e " Backend logs:"
echo "   gcloud logging read 'resource.labels.service_name=\"${BACKEND_SERVICE}\"' --limit=50 --project=${PROJECT_ID}"
echo ""
echo -e " Rollback:"
echo "   gcloud run services describe ${BACKEND_SERVICE} --region=${REGION} --format='value(status.latestReadyRevisionName)'"
echo ""
