#!/bin/bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
CLUSTER_ID="telenova-alloydb-cluster"
INSTANCE_ID="telenova-alloydb-primary"
DATABASE_NAME="telenova"
DB_USER="telenova"
NETWORK="default"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: GOOGLE_CLOUD_PROJECT environment variable is required."
  exit 1
fi

if [[ -z "${ALLOYDB_PASSWORD:-}" ]]; then
  echo "ERROR: Set ALLOYDB_PASSWORD environment variable before running this script."
  exit 1
fi

echo "=== TeleNova AI Support - AlloyDB Provisioning ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Cluster: ${CLUSTER_ID}"
echo ""

echo "[1/5] Enabling required APIs..."
gcloud services enable alloydb.googleapis.com \
  servicenetworking.googleapis.com \
  --project "${PROJECT_ID}"

echo "[2/5] Creating AlloyDB cluster..."
if ! gcloud alloydb clusters describe "${CLUSTER_ID}" \
  --region "${REGION}" --project "${PROJECT_ID}" &>/dev/null; then
  gcloud alloydb clusters create "${CLUSTER_ID}" \
    --region "${REGION}" \
    --network "${NETWORK}" \
    --password "${ALLOYDB_PASSWORD}" \
    --project "${PROJECT_ID}"
  echo "Cluster created."
else
  echo "Cluster already exists, skipping creation."
fi

echo "[3/5] Creating AlloyDB primary instance..."
if ! gcloud alloydb instances describe "${INSTANCE_ID}" \
  --cluster "${CLUSTER_ID}" --region "${REGION}" --project "${PROJECT_ID}" &>/dev/null; then
  gcloud alloydb instances create "${INSTANCE_ID}" \
    --cluster "${CLUSTER_ID}" \
    --region "${REGION}" \
    --instance-type PRIMARY \
    --cpu-count 4 \
    --database-flags alloydb.enable_pgvector=on \
    --project "${PROJECT_ID}"
  echo "Primary instance created with pgvector (AlloyDB AI) enabled."
else
  echo "Instance already exists, skipping creation."
fi

INSTANCE_IP=$(gcloud alloydb instances describe "${INSTANCE_ID}" \
  --cluster "${CLUSTER_ID}" --region "${REGION}" --project "${PROJECT_ID}" \
  --format "value(ipAddress)")

echo "[4/5] Running schema migrations..."
PGPASSWORD="${ALLOYDB_PASSWORD}" psql \
  -h "${INSTANCE_IP}" -U postgres -d postgres -c \
  "CREATE DATABASE ${DATABASE_NAME};" || echo "Database may already exist, continuing."

PGPASSWORD="${ALLOYDB_PASSWORD}" psql \
  -h "${INSTANCE_IP}" -U postgres -d "${DATABASE_NAME}" \
  -f app/db/migrations/001_core_schema.sql

PGPASSWORD="${ALLOYDB_PASSWORD}" psql \
  -h "${INSTANCE_IP}" -U postgres -d "${DATABASE_NAME}" \
  -f app/db/migrations/002_seed_data.sql

echo "[5/5] Provisioning complete."
echo ""
echo "=== AlloyDB Cluster Ready ==="
echo "Instance IP: ${INSTANCE_IP}"
echo "Database: ${DATABASE_NAME}"
echo ""
echo "Set the following environment variables for Cloud Run deployment:"
echo "  DATABASE_URL=postgresql://postgres:${ALLOYDB_PASSWORD}@${INSTANCE_IP}:5432/${DATABASE_NAME}"
echo ""
echo "For private connectivity from Cloud Run, configure a Serverless VPC Access connector"
echo "and the AlloyDB Auth Proxy sidecar, or use the AlloyDB Language Connectors."
