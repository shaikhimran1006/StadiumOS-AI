#!/usr/bin/env bash
# ============================================================================
# StadiumOS AI - GCP Project Setup Script
# Sets up all required GCP resources for the StadiumOS AI platform
# Usage: ./scripts/setup-gcp.sh [project-id] [region]
# ============================================================================
set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID="${1:-stadiumos-ai-prod}"
REGION="${2:-us-central1}"
REPOSITORY="stadiumos"
BACKEND_SA="stadiumos-backend"
FRONTEND_SA="stadiumos-frontend"
CI_SA="stadiumos-ci"
FIRESTORE_DB="(default)"
BIGQUERY_DATASET="stadium_analytics"
STORAGE_BUCKET="${PROJECT_ID}-assets"
VPC_CONNECTOR="stadiumos-vpc-connector"
LOG_BUCKET="${PROJECT_ID}-logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

step() { echo -e "\n${GREEN}==>${NC} $1"; }

# ============================================================================
# Pre-flight checks
# ============================================================================
step "Verifying prerequisites"

if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1 > /dev/null 2>&1; then
    log_error "Not authenticated. Run: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1)
log_ok "Authenticated as: ${ACTIVE_ACCOUNT}"

gcloud config set project "${PROJECT_ID}" 2>/dev/null || {
    log_warn "Project ${PROJECT_ID} not found. Creating..."
    gcloud projects create "${PROJECT_ID}" --name="StadiumOS AI" --labels=team=platform
    gcloud billing accounts list --format="value(name)" | head -1 | xargs -I {} \
        gcloud billing projects link "${PROJECT_ID}" --billing-account={}
    gcloud config set project "${PROJECT_ID}"
}
log_ok "Project: ${PROJECT_ID}"

# ============================================================================
# Step 1: Enable Required APIs
# ============================================================================
step "Enabling required GCP APIs"

APIS=(
    "run.googleapis.com"
    "firestore.googleapis.com"
    "pubsub.googleapis.com"
    "bigquery.googleapis.com"
    "storage.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
    "cloudtrace.googleapis.com"
    "compute.googleapis.com"
    "vpcaccess.googleapis.com"
    "containeranalysis.googleapis.com"
    "binaryauthorization.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "Enabling ${api}..."
    gcloud services enable "${api}" --project="${PROJECT_ID}" --quiet 2>/dev/null || log_warn "Failed to enable ${api}"
done
log_ok "APIs enabled"

# Wait for APIs to propagate
sleep 10

# ============================================================================
# Step 2: Create Service Accounts
# ============================================================================
step "Creating service accounts"

create_sa() {
    local name=$1
    local display_name=$2
    local email="${name}@${PROJECT_ID}.iam.gserviceaccount.com"

    if gcloud iam service-accounts describe "${email}" --project="${PROJECT_ID}" &>/dev/null; then
        log_ok "Service account already exists: ${email}"
    else
        gcloud iam service-accounts create "${name}" \
            --display-name="${display_name}" \
            --project="${PROJECT_ID}"
        log_ok "Created: ${email}"
    fi
}

create_sa "${BACKEND_SA}" "StadiumOS Backend Service Account"
create_sa "${FRONTEND_SA}" "StadiumOS Frontend Service Account"
create_sa "${CI_SA}" "StadiumOS CI/CD Service Account"

# ============================================================================
# Step 3: Set IAM Policies
# ============================================================================
step "Setting IAM policies"

# Backend SA roles
BACKEND_ROLES=(
    "roles/datastore.user"
    "roles/pubsub.publisher"
    "roles/pubsub.subscriber"
    "roles/bigquery.dataEditor"
    "roles/storage.objectViewer"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
    "roles/cloudtrace.agent"
)

for role in "${BACKEND_ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}" \
        --quiet 2>/dev/null
    log_ok "Granted ${role} to ${BACKEND_SA}"
done

# Frontend SA roles
FRONTEND_ROLES=(
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
    "roles/storage.objectViewer"
)

for role in "${FRONTEND_ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${FRONTEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}" \
        --quiet 2>/dev/null
    log_ok "Granted ${role} to ${FRONTEND_SA}"
done

# CI SA roles
CI_ROLES=(
    "roles/run.admin"
    "roles/artifactregistry.writer"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/logging.logWriter"
)

for role in "${CI_ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${CI_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}" \
        --quiet 2>/dev/null
    log_ok "Granted ${role} to ${CI_SA}"
done

# ============================================================================
# Step 4: Create Firestore Database
# ============================================================================
step "Creating Firestore database"

if gcloud firestore databases describe --project="${PROJECT_ID}" --location="${REGION}" &>/dev/null; then
    log_ok "Firestore database already exists"
else
    gcloud firestore databases create \
        --project="${PROJECT_ID}" \
        --location="${REGION}" \
        --type=firestore-native \
        --quiet
    log_ok "Firestore database created in ${REGION}"
fi

# ============================================================================
# Step 5: Create Pub/Sub Topics and Subscriptions
# ============================================================================
step "Creating Pub/Sub topics and subscriptions"

TOPICS=(
    "game-events"
    "player-updates"
    "analytics-events"
    "ai-predictions"
    "user-notifications"
)

SUBSCRIPTIONS=(
    "game-events-sub:game-events"
    "player-updates-sub:player-updates"
    "analytics-events-sub:analytics-events"
    "ai-predictions-sub:ai-predictions"
    "user-notifications-sub:user-notifications"
)

for topic in "${TOPICS[@]}"; do
    if gcloud pubsub topics describe "${topic}" --project="${PROJECT_ID}" &>/dev/null; then
        log_ok "Topic already exists: ${topic}"
    else
        gcloud pubsub topics create "${topic}" --project="${PROJECT_ID}"
        log_ok "Created topic: ${topic}"
    fi
done

for sub_info in "${SUBSCRIPTIONS[@]}"; do
    IFS=':' read -r sub_name topic_name <<< "${sub_info}"
    if gcloud pubsub subscriptions describe "${sub_name}" --project="${PROJECT_ID}" &>/dev/null; then
        log_ok "Subscription already exists: ${sub_name}"
    else
        gcloud pubsub subscriptions create "${sub_name}" \
            --topic="${topic_name}" \
            --project="${PROJECT_ID}" \
            --ack-deadline=60 \
            --max-delivery-attempts=5 \
            --dead-letter-topic="${topic_name}-dead-letter"
        log_ok "Created subscription: ${sub_name} -> ${topic_name}"
    fi
done

# ============================================================================
# Step 6: Create BigQuery Dataset
# ============================================================================
step "Creating BigQuery dataset"

if bq show --project="${PROJECT_ID}" "${BIGQUERY_DATASET}" &>/dev/null; then
    log_ok "BigQuery dataset already exists: ${BIGQUERY_DATASET}"
else
    bq mk --project="${PROJECT_ID}" \
        --dataset \
        --location="${REGION}" \
        --description="StadiumOS Analytics Data" \
        --label="team:platform" \
        "${BIGQUERY_DATASET}"
    log_ok "Created BigQuery dataset: ${BIGQUERY_DATASET}"

    # Create tables
    TABLES=(
        "game_stats:Game statistics and play-by-play data"
        "player_stats:Player performance metrics over time"
        "user_events:User interaction and analytics events"
        "predictions:AI model predictions and outcomes"
    )

    for table_info in "${TABLES[@]}"; do
        IFS=':' read -r table_name description <<< "${table_info}"
        bq mk --project="${PROJECT_ID}" \
            --table \
            --description="${description}" \
            "${BIGQUERY_DATASET}.${table_name}" \
            2>/dev/null || log_warn "Table ${table_name} may already exist"
        log_ok "Table: ${BIGQUERY_DATASET}.${table_name}"
    done
fi

# ============================================================================
# Step 7: Create Cloud Storage Buckets
# ============================================================================
step "Creating Cloud Storage buckets"

BUCKETS=(
    "${STORAGE_BUCKET}:StadiumOS Static Assets"
    "${PROJECT_ID}-backups:StadiumOS Database Backups"
    "${PROJECT_ID}-ml-models:StadiumOS ML Model Artifacts"
    "${LOG_BUCKET}:StadiumOS Audit Logs"
)

for bucket_info in "${BUCKETS[@]}"; do
    IFS=':' read -r bucket_name description <<< "${bucket_info}"
    if gsutil ls -b "gs://${bucket_name}" &>/dev/null; then
        log_ok "Bucket already exists: gs://${bucket_name}"
    else
        gsutil mb -p "${PROJECT_ID}" \
            -l "${REGION}" \
            -c standard \
            -b on \
            --default-storage-class=STANDARD \
            --uniform-bucket-level-access \
            "gs://${bucket_name}"
        gsutil versioning set on "gs://${bucket_name}"
        log_ok "Created bucket: gs://${bucket_name}"
    fi
done

# Set CORS on assets bucket
cat > /tmp/cors.json << 'CORS_EOF'
[
  {
    "origin": ["https://stadiumos-ai.web.app", "http://localhost:5173"],
    "method": ["GET", "HEAD", "OPTIONS"],
    "responseHeader": ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"],
    "maxAgeSeconds": 3600
  }
]
CORS_EOF
gsutil cors set /tmp/cors.json "gs://${STORAGE_BUCKET}"
rm -f /tmp/cors.json

# ============================================================================
# Step 8: Create Artifact Registry Repository
# ============================================================================
step "Creating Artifact Registry repository"

if gcloud artifacts repositories describe "${REPOSITORY}" \
    --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    log_ok "Artifact Registry repository already exists: ${REPOSITORY}"
else
    gcloud artifacts repositories create "${REPOSITORY}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="StadiumOS AI Container Images" \
        --project="${PROJECT_ID}"
    log_ok "Created Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}"

    # Grant SA access to pull images
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/artifactregistry.reader" \
        --quiet 2>/dev/null

    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${FRONTEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/artifactregistry.reader" \
        --quiet 2>/dev/null
fi

# ============================================================================
# Step 9: Configure Docker for Artifact Registry
# ============================================================================
step "Configuring Docker authentication"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
log_ok "Docker configured for Artifact Registry"

# ============================================================================
# Step 10: Create VPC Connector (for Cloud Run -> Firestore)
# ============================================================================
step "Creating VPC Access Connector"

if gcloud compute networks vpc-access connectors describe "${VPC_CONNECTOR}" \
    --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    log_ok "VPC connector already exists: ${VPC_CONNECTOR}"
else
    gcloud compute networks vpc-access connectors create "${VPC_CONNECTOR}" \
        --network=default \
        --region="${REGION}" \
        --range=10.8.0.0/28 \
        --min-instances=2 \
        --max-instances=10 \
        --project="${PROJECT_ID}"
    log_ok "Created VPC connector: ${VPC_CONNECTOR}"
fi

# ============================================================================
# Step 11: Create Secret Manager Secrets
# ============================================================================
step "Creating Secret Manager secrets"

SECRETS=(
    "stadiumos-jwt-secret"
    "stadiumos-encryption-key"
    "stadiumos-firebase-credentials"
)

for secret in "${SECRETS[@]}"; do
    if gcloud secrets describe "${secret}" --project="${PROJECT_ID}" &>/dev/null; then
        log_ok "Secret already exists: ${secret}"
    else
        echo -n "placeholder-replace-with-real-value" | \
            gcloud secrets create "${secret}" \
                --data-file=- \
                --project="${PROJECT_ID}" \
                --replication-policy="automatic"
        log_ok "Created secret: ${secret}"
        log_warn "Remember to update secret values with real credentials"
    fi

    # Grant access to backend SA
    gcloud secrets add-iam-policy-binding "${secret}" \
        --member="serviceAccount:${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet 2>/dev/null
done

# ============================================================================
# Step 12: Set up Firewall Rules
# ============================================================================
step "Configuring network settings"

# Allow Cloud Run health checks
if ! gcloud compute firewall-rules describe "allow-cloud-run-healthchecks" \
    --project="${PROJECT_ID}" &>/dev/null; then
    gcloud compute firewall-rules create "allow-cloud-run-healthchecks" \
        --network=default \
        --allow=tcp:8080 \
        --source-ranges=130.211.0.0/22,35.191.0.0/16 \
        --target-tags=cloud-run \
        --project="${PROJECT_ID}" \
        2>/dev/null || log_warn "Firewall rule creation skipped"
fi

# ============================================================================
# Step 13: Create Cloud Monitoring Alerting Channel (email placeholder)
# ============================================================================
step "Setting up Cloud Monitoring"

# Import the dashboard
if [ -f "deploy/monitoring/dashboard.json" ]; then
    gcloud monitoring dashboards create \
        --config-from-file=deploy/monitoring/dashboard.json \
        --project="${PROJECT_ID}" 2>/dev/null || log_ok "Dashboard may already exist"
    log_ok "Monitoring dashboard created"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN} StadiumOS AI - GCP Setup Complete${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e " Project:            ${BLUE}${PROJECT_ID}${NC}"
echo -e " Region:             ${BLUE}${REGION}${NC}"
echo -e " Artifact Registry:  ${BLUE}${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}${NC}"
echo -e " Firestore:          ${BLUE}${REGION} (${FIRESTORE_DB})${NC}"
echo -e " BigQuery Dataset:   ${BLUE}${BIGQUERY_DATASET}${NC}"
echo -e " Storage Bucket:     ${BLUE}gs://${STORAGE_BUCKET}${NC}"
echo -e " Backend SA:         ${BLUE}${BACKEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
echo -e " Frontend SA:        ${BLUE}${FRONTEND_SA}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
echo -e " CI SA:              ${BLUE}${CI_SA}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
echo -e " VPC Connector:      ${BLUE}${VPC_CONNECTOR}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Update Secret Manager secrets with real values"
echo "  2. Run: make deploy-staging"
echo "  3. Deploy Firestore rules: firebase deploy --only firestore:rules"
echo ""
