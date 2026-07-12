# StadiumOS AI - Deployment Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend build |
| Docker | 24+ | Container builds |
| Docker Compose | 2.x | Local development |
| Google Cloud SDK | latest | GCP deployment |
| Firebase CLI | latest | Firestore rules |

## GCP Project Setup

### Step 1: Create Project

```bash
gcloud projects create stadiumos-ai-prod --name="StadiumOS AI"
gcloud config set project stadiumos-ai-prod
gcloud billing account list
gcloud billing projects link stadiumos-ai-prod --billing-account=ACCOUNT_ID
```

### Step 2: Enable APIs

```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  translate.googleapis.com \
  speech.googleapis.com \
  vision.googleapis.com \
  maps-backend.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudscheduler.googleapis.com
```

### Step 3: Set Up Firestore

```bash
gcloud firestore databases create --location=us-central1
```

### Step 4: Create Service Account

```bash
gcloud iam service-accounts create stadiumos-backend \
  --display-name="StadiumOS Backend Service Account"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/cloudtranslate.user"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/speech.client"

gcloud projects add-iam-policy-binding stadiumos-ai-prod \
  --member="serviceAccount:stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud iam service-accounts keys create key.json \
  --iam-account=stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com
```

### Step 5: Create Pub/Sub Topics

```bash
gcloud pubsub topics create stadiumos-alerts
gcloud pubsub topics create stadiumos-analytics
gcloud pubsub topics create stadiumos-notifications

gcloud pubsub subscriptions create stadiumos-alerts-sub \
  --topic=stadiumos-alerts
```

### Step 6: Create BigQuery Dataset

```bash
bq mk --dataset stadiumos_analytics

bq mk --table stadiumos_analytics.ai_conversations \
  conversation_id:STRING,user_id:STRING,channel:STRING,language:STRING,\
  message_count:INTEGER,status:STRING,latency_ms:INTEGER,timestamp:TIMESTAMP

bq mk --table stadiumos_analytics.ai_messages \
  message_id:STRING,conversation_id:STRING,sender_type:STRING,\
  agent:STRING,confidence:FLOAT,latency_ms:INTEGER,timestamp:TIMESTAMP

bq mk --table stadiumos_analytics.alert_events \
  alert_id:STRING,alert_type:STRING,priority:INTEGER,status:STRING,\
  stadium_id:STRING,action:STRING,timestamp:TIMESTAMP

bq mk --table stadiumos_analytics.fan_events \
  event_id:STRING,user_id:STRING,event_type:STRING,\
  metadata:STRING,timestamp:TIMESTAMP

bq mk --table stadiumos_analytics.platform_metrics \
  metric_name:STRING,value:FLOAT,labels:STRING,timestamp:TIMESTAMP
```

### Step 7: Create GCS Buckets

```bash
gsutil mb -l us-central1 gs://stadiumos-media
gsutil mb -l us-central1 gs://stadiumos-documents
gsutil mb -l us-central1 gs://stadiumos-backups
```

### Step 8: Store Secrets

```bash
echo -n "your-64-char-jwt-secret-key-here" | \
  gcloud secrets create jwt-secret-key --data-file=-

echo -n "your-oauth2-client-secret" | \
  gcloud secrets create oauth2-client-secret --data-file=-

echo -n "your-google-maps-api-key" | \
  gcloud secrets create google-maps-api-key --data-file=-
```

---

## Local Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/your-org/stadiumos-ai.git
cd stadiumos-ai

cp .env.example .env
# Edit .env with your values

make install
```

### 2. Start with Docker Compose

```bash
make dev
```

This starts:
- Backend on `http://localhost:8000`
- Frontend on `http://localhost:5173`
- Firestore Emulator on `http://localhost:8180`
- Pub/Sub Emulator on `http://localhost:8280`

### 3. Start Backend Only (no Docker)

```bash
# Start Firestore emulator
gcloud beta emulators firestore --host-port=localhost:8180 start &

# Start backend
make dev-backend
```

---

## Docker Deployment

### Build Images

```bash
make docker-build
```

### Run Locally

```bash
make docker-up-d
make docker-logs
```

### Stop

```bash
make docker-down
```

---

## Cloud Run Deployment

### Build and Push to Artifact Registry

```bash
gcloud artifacts repositories create stadiumos-docker \
  --repository-format=docker \
  --location=us-central1

# Backend
gcloud builds submit --tag \
  us-central1-docker.pkg.dev/stadiumos-ai-prod/stadiumos-docker/stadiumos-backend:latest \
  --config backend/cloudbuild.yaml .

# Frontend
gcloud builds submit --tag \
  us-central1-docker.pkg.dev/stadiumos-ai-prod/stadiumos-docker/stadiumos-frontend:latest \
  --config frontend/cloudbuild.yaml .
```

### Deploy Backend

```bash
gcloud run deploy stadiumos-backend \
  --image=us-central1-docker.pkg.dev/stadiumos-ai-prod/stadiumos-docker/stadiumos-backend:latest \
  --region=us-central1 \
  --service-account=stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=80 \
  --timeout=300 \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=stadiumos-ai-prod,GCP_REGION=us-central1"
```

### Deploy Frontend

```bash
gcloud run deploy stadiumos-frontend \
  --image=us-central1-docker.pkg.dev/stadiumos-ai-prod/stadiumos-docker/stadiumos-frontend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=5 \
  --memory=256Mi
```

---

## CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/deploy.yaml`)

```yaml
name: Deploy

on:
  push:
    branches: [main]

env:
  PROJECT_ID: stadiumos-ai-prod
  REGION: us-central1
  BACKEND_IMAGE: stadiumos-backend
  FRONTEND_IMAGE: stadiumos-frontend

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run tests
        run: cd backend && python -m pytest tests/ -v --tb=short
      - name: Lint
        run: cd backend && python -m ruff check .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - name: Build and push backend
        run: |
          gcloud builds submit --tag \
            ${REGION}-docker.pkg.dev/${PROJECT_ID}/stadiumos-docker/${BACKEND_IMAGE}:${{ github.sha }} \
            -f backend/Dockerfile backend/
      - name: Deploy backend to Cloud Run
        run: |
          gcloud run deploy ${BACKEND_IMAGE} \
            --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/stadiumos-docker/${BACKEND_IMAGE}:${{ github.sha }} \
            --region=${REGION} \
            --service-account=stadiumos-backend@${PROJECT_ID}.iam.gserviceaccount.com
```

---

## Monitoring Setup

### Cloud Monitoring Dashboard

```bash
gcloud monitoring dashboards create --config-from-file=deploy/dashboard.json
```

### Key Metrics to Monitor

| Metric | Alert Threshold |
|--------|-----------------|
| Request latency (p99) | > 2s |
| Error rate (5xx) | > 1% |
| AI response latency | > 5s |
| Firestore reads/writes | > 80% quota |
| Pub/Sub unacked messages | > 1000 |
| Container CPU utilization | > 80% |
| Container memory utilization | > 85% |

### Log-Based Alerts

```bash
gcloud logging metrics create error_rate \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR' \
  --description="Cloud Run error count"
```

---

## Scaling Configuration

### Cloud Run Autoscaling

```bash
gcloud run services update stadiumos-backend \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=80 \
  --cpu=2 \
  --memory=1Gi
```

### Firestore Scaling

Firestore auto-scales. Monitor:
- Read/write operations per second
- Storage size
- Index size

### BigQuery Scaling

- Partition tables by `timestamp` column
- Use partition pruning in queries
- Set table expiration for raw event tables

---

## Backup and Recovery

### Firestore Backup

```bash
gcloud firestore export gs://stadiumos-backups/firestore/$(date +%Y%m%d)
```

### Scheduled Backups

```bash
gcloud scheduler jobs create http firestore-backup \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/stadiumos-ai-prod/databases/(default):exportDocuments" \
  --http-method=POST \
  --service-account=stadiumos-backend@stadiumos-ai-prod.iam.gserviceaccount.com
```

### BigQuery Backup

```bash
bq cp stadiumos_analytics.ai_conversations \
  stadiumos_analytics.ai_conversations_backup_$(date +%Y%m%d)
```

### Recovery Steps

1. **Firestore**: Import from GCS export
   ```bash
   gcloud firestore import gs://stadiumos-backups/firestore/BACKUP_DATE
   ```

2. **BigQuery**: Copy from backup tables

3. **Pub/Sub**: Messages are retained per subscription configuration (default 7 days)

4. **GCS**: Enable object versioning for document recovery
   ```bash
   gsutil versioning set on gs://stadiumos-documents
   ```
