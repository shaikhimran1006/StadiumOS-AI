#!/usr/bin/env bash
# ============================================================================
# StadiumOS AI - Data Seeding Script
# Seeds Firestore with initial data for development/staging
# Usage: ./scripts/seed-data.sh [environment]
# ============================================================================
set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
ENVIRONMENT="${1:-development}"
PROJECT_ID="${GCP_PROJECT_ID:-stadiumos-ai-${ENVIRONMENT}}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

step() { echo -e "\n${GREEN}==>${NC} $1"; }

# ============================================================================
# Check for emulators or live project
# ============================================================================
if [ "${ENVIRONMENT}" = "development" ]; then
    if [ -n "${FIRESTORE_EMULATOR_HOST:-}" ]; then
        log_info "Using Firestore emulator at ${FIRESTORE_EMULATOR_HOST}"
    else
        log_warn "FIRESTORE_EMULATOR_HOST not set. Setting to localhost:8180"
        export FIRESTORE_EMULATOR_HOST="localhost:8180"
    fi
fi

# Use the Python seed script if available
if [ -f "backend/scripts/seed_firestore.py" ]; then
    step "Running Python seed script"
    python backend/scripts/seed_firestore.py --environment "${ENVIRONMENT}"
    exit 0
fi

# Otherwise, use gcloud Firestore batch commands
step "Seeding Firestore data for: ${ENVIRONMENT}"

# Create a temp directory for seed data
SEED_DIR=$(mktemp -d)
trap "rm -rf ${SEED_DIR}" EXIT

# ============================================================================
# Seed: Stadiums
# ============================================================================
step "Seeding stadiums"

cat > "${SEED_DIR}/stadiums.json" << 'STADIUMS_EOF'
[
  {
    "name": "MetLife Stadium",
    "location": "East Rutherford, NJ",
    "capacity": 82500,
    "surface": "Synthetic Turf",
    "opened": 2010,
    "teams": ["New York Giants", "New York Jets"],
    "latitude": 40.8135,
    "longitude": -74.0745,
    "timezone": "America/New_York",
    "features": ["retractable_roof", "luxury_suites", "video_board"],
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "SoFi Stadium",
    "location": "Inglewood, CA",
    "capacity": 70240,
    "surface": "Synthetic Turf",
    "opened": 2020,
    "teams": ["Los Angeles Rams", "Los Angeles Chargers"],
    "latitude": 33.9534,
    "longitude": -118.3387,
    "timezone": "America/Los_Angeles",
    "features": ["retractable_roof", "infinity_screen", "luxury_suites"],
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "AT&T Stadium",
    "location": "Arlington, TX",
    "capacity": 80000,
    "surface": "Synthetic Turf",
    "opened": 2009,
    "teams": ["Dallas Cowboys"],
    "latitude": 32.7473,
    "longitude": -97.0945,
    "timezone": "America/Chicago",
    "features": ["retractable_roof", "center_hung_video_board", "patio"],
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "Lambeau Field",
    "location": "Green Bay, WI",
    "capacity": 81441,
    "surface": "Synthetic Turf",
    "opened": 1957,
    "teams": ["Green Bay Packers"],
    "latitude": 44.5013,
    "longitude": -88.0622,
    "timezone": "America/Chicago",
    "features": ["outdoor", "historic", "frozen_tundra"],
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "Arrowhead Stadium",
    "location": "Kansas City, MO",
    "capacity": 76416,
    "surface": "Synthetic Turf",
    "opened": 1972,
    "teams": ["Kansas City Chiefs"],
    "latitude": 39.0489,
    "longitude": -94.4839,
    "timezone": "America/Chicago",
    "features": ["outdoor", "loudest_stadium", "heritage"],
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  }
]
STADIUMS_EOF
log_ok "Stadium data prepared (5 stadiums)"

# ============================================================================
# Seed: Teams
# ============================================================================
step "Seeding teams"

cat > "${SEED_DIR}/teams.json" << 'TEAMS_EOF'
[
  {
    "name": "Kansas City Chiefs",
    "abbreviation": "KC",
    "conference": "AFC",
    "division": "West",
    "city": "Kansas City",
    "state": "MO",
    "stadium": "Arrowhead Stadium",
    "headCoach": "Andy Reid",
    "primaryColor": "#E31837",
    "secondaryColor": "#FFB81C",
    "founded": 1960,
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "San Francisco 49ers",
    "abbreviation": "SF",
    "conference": "NFC",
    "division": "West",
    "city": "San Francisco",
    "state": "CA",
    "stadium": "Levi's Stadium",
    "headCoach": "Kyle Shanahan",
    "primaryColor": "#AA0000",
    "secondaryColor": "#B3995D",
    "founded": 1946,
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "Dallas Cowboys",
    "abbreviation": "DAL",
    "conference": "NFC",
    "division": "East",
    "city": "Arlington",
    "state": "TX",
    "stadium": "AT&T Stadium",
    "headCoach": "Mike McCarthy",
    "primaryColor": "#003594",
    "secondaryColor": "#869397",
    "founded": 1960,
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "Buffalo Bills",
    "abbreviation": "BUF",
    "conference": "AFC",
    "division": "East",
    "city": "Orchard Park",
    "state": "NY",
    "stadium": "Highmark Stadium",
    "headCoach": "Sean McDermott",
    "primaryColor": "#00338D",
    "secondaryColor": "#C60C30",
    "founded": 1960,
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "name": "Baltimore Ravens",
    "abbreviation": "BAL",
    "conference": "AFC",
    "division": "North",
    "city": "Baltimore",
    "state": "MD",
    "stadium": "M&T Bank Stadium",
    "headCoach": "John Harbaugh",
    "primaryColor": "#241773",
    "secondaryColor": "#9E7C0C",
    "founded": 1996,
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  }
]
TEAMS_EOF
log_ok "Team data prepared (5 teams)"

# ============================================================================
# Seed: Players
# ============================================================================
step "Seeding players"

cat > "${SEED_DIR}/players.json" << 'PLAYERS_EOF'
[
  {
    "firstName": "Patrick",
    "lastName": "Mahomes",
    "position": "QB",
    "number": 15,
    "teamId": "KC",
    "age": 28,
    "height": "6-2",
    "weight": 230,
    "college": "Texas Tech",
    "yearsPro": 7,
    "overallRating": 99,
    "speed": 88,
    "accuracy": 97,
    "power": 95,
    "awareness": 98,
    "form": 95,
    "injuryRisk": 15,
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "firstName": "Brock",
    "lastName": "Purdy",
    "position": "QB",
    "number": 13,
    "teamId": "SF",
    "age": 24,
    "height": "6-1",
    "weight": 220,
    "college": "Iowa State",
    "yearsPro": 2,
    "overallRating": 91,
    "speed": 78,
    "accuracy": 92,
    "power": 82,
    "awareness": 88,
    "form": 90,
    "injuryRisk": 20,
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "firstName": "Josh",
    "lastName": "Allen",
    "position": "QB",
    "number": 17,
    "teamId": "BUF",
    "age": 27,
    "height": "6-5",
    "weight": 245,
    "college": "Wyoming",
    "yearsPro": 6,
    "overallRating": 97,
    "speed": 90,
    "accuracy": 93,
    "power": 98,
    "awareness": 92,
    "form": 93,
    "injuryRisk": 18,
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "firstName": "Lamar",
    "lastName": "Jackson",
    "position": "QB",
    "number": 8,
    "teamId": "BAL",
    "age": 27,
    "height": "6-2",
    "weight": 212,
    "college": "Louisville",
    "yearsPro": 6,
    "overallRating": 96,
    "speed": 97,
    "accuracy": 90,
    "power": 88,
    "awareness": 90,
    "form": 92,
    "injuryRisk": 25,
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  {
    "firstName": "Dak",
    "lastName": "Prescott",
    "position": "QB",
    "number": 4,
    "teamId": "DAL",
    "age": 31,
    "height": "6-2",
    "weight": 238,
    "college": "Mississippi State",
    "yearsPro": 8,
    "overallRating": 88,
    "speed": 75,
    "accuracy": 89,
    "power": 86,
    "awareness": 87,
    "form": 85,
    "injuryRisk": 30,
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  }
]
PLAYERS_EOF
log_ok "Player data prepared (5 players)"

# ============================================================================
# Seed: Announcements
# ============================================================================
step "Seeding announcements"

cat > "${SEED_DIR}/announcements.json" << 'ANNOUNCEMENTS_EOF'
[
  {
    "title": "Welcome to StadiumOS AI",
    "content": "Welcome to the StadiumOS AI platform! Experience next-generation stadium management powered by artificial intelligence.",
    "type": "info",
    "active": true,
    "priority": 1,
    "createdAt": "2024-01-01T00:00:00Z",
    "expiresAt": "2025-12-31T23:59:59Z"
  },
  {
    "title": "AI Predictions Now Live",
    "content": "Our AI prediction engine is now live. Get real-time game predictions powered by machine learning.",
    "type": "update",
    "active": true,
    "priority": 2,
    "createdAt": "2024-06-01T00:00:00Z",
    "expiresAt": "2025-12-31T23:59:59Z"
  },
  {
    "title": "Season 2024 Preview",
    "content": "Get ready for an exciting season! New features include real-time chat, player trading, and enhanced analytics.",
    "type": "promotion",
    "active": true,
    "priority": 3,
    "createdAt": "2024-08-01T00:00:00Z",
    "expiresAt": "2025-03-01T00:00:00Z"
  }
]
ANNOUNCEMENTS_EOF
log_ok "Announcement data prepared (3 announcements)"

# ============================================================================
# Write data to Firestore using Python (available in the backend env)
# ============================================================================
step "Writing data to Firestore"

if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    PYTHON_CMD=$(command -v python3 || command -v python)

    cat > "${SEED_DIR}/seed_firestore.py" << 'PYTHON_EOF'
import json
import os
import sys
import glob

try:
    from google.cloud import firestore
except ImportError:
    print("google-cloud-firestore not installed. Install with: pip install google-cloud-firestore")
    sys.exit(1)

SEED_DIR = os.path.dirname(os.path.abspath(__file__))

db = firestore.Client()

COLLECTIONS = {
    "stadiums": "stadiums.json",
    "teams": "teams.json",
    "players": "players.json",
    "announcements": "announcements.json",
}

for collection_name, filename in COLLECTIONS.items():
    filepath = os.path.join(SEED_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  Skipping {collection_name}: file not found")
        continue

    with open(filepath, "r") as f:
        documents = json.load(f)

    batch = db.batch()
    count = 0

    for doc in documents:
        doc_id = doc.pop("id", None) or f"{collection_name}_{count + 1}"
        doc_ref = db.collection(collection_name).document(doc_id)
        batch.set(doc_ref, doc)
        count += 1

        if count % 500 == 0:
            batch.commit()
            batch = db.batch()
            print(f"  Written {count} documents to {collection_name}...")

    batch.commit()
    print(f"  Seeded {count} documents into '{collection_name}'")

print("\nFirestore seeding complete!")
PYTHON_EOF

    ${PYTHON_CMD} "${SEED_DIR}/seed_firestore.py"
    log_ok "Data seeded to Firestore"
else
    log_warn "Python not found. Data files prepared in ${SEED_DIR}"
    log_warn "To seed manually, install google-cloud-firestore and run the seed script"
    cp "${SEED_DIR}"/*.json . 2>/dev/null || true
fi

# ============================================================================
# Seed BigQuery (if authenticated and connected)
# ============================================================================
if [ "${ENVIRONMENT}" != "development" ]; then
    step "Seeding BigQuery analytics tables"

    bq query --project_id="${PROJECT_ID}" --use_legacy_sql=false << 'BQ_SEED' 2>/dev/null || log_warn "BigQuery seeding skipped (not authenticated)"
INSERT INTO `stadium_analytics.user_events` (event_id, event_name, user_id, session_id, category, properties, timestamp)
VALUES
  ('seed-001', 'app_launch', NULL, 'seed-session', 'NAVIGATION', '{"platform": "web"}', TIMESTAMP('2024-01-01T00:00:00Z')),
  ('seed-002', 'page_view', NULL, 'seed-session', 'NAVIGATION', '{"page": "/games"}', TIMESTAMP('2024-01-01T00:00:05Z')),
  ('seed-003', 'game_view_start', NULL, 'seed-session', 'GAME_VIEW', '{"gameId": "game_001"}', TIMESTAMP('2024-01-01T00:00:10Z'))
BQ_SEED
    log_ok "BigQuery seed data inserted"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN} StadiumOS AI - Data Seeding Complete${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e " Environment: ${BLUE}${ENVIRONMENT}${NC}"
echo -e " Project:     ${BLUE}${PROJECT_ID}${NC}"
echo ""
echo -e " Seeded collections:"
echo "   - stadiums (5)"
echo "   - teams (5)"
echo "   - players (5)"
echo "   - announcements (3)"
echo ""
