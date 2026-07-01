#!/bin/bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="telanova-support-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
GCS_BUCKET="${GCS_BUCKET_NAME:-telanova-support-knowledge-base}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: GOOGLE_CLOUD_PROJECT environment variable is required."
  exit 1
fi

echo "=== TeleNova AI Support - Cloud Run Deployment ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

echo "[1/5] Authenticating with Google Cloud..."
gcloud auth configure-docker --quiet

echo "[2/5] Building Docker image..."
docker build -t "${IMAGE_NAME}:latest" .
docker push "${IMAGE_NAME}:latest"

echo "[3/5] Creating GCS bucket for knowledge base..."
if ! gsutil ls "gs://${GCS_BUCKET}" &>/dev/null; then
  gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${GCS_BUCKET}"
  echo "Created bucket gs://${GCS_BUCKET}"
fi

echo "[4/5] Uploading knowledge base documents..."
gsutil -m cp knowledge_base/*.md "gs://${GCS_BUCKET}/knowledge_base/"

echo "[5/5] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}:latest" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 60 \
  --concurrency 80 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars "GOOGLE_CLOUD_LOCATION=${REGION}" \
  --set-env-vars "APP_ENV=production" \
  --set-env-vars "GCS_BUCKET_NAME=${GCS_BUCKET}" \
  --labels "app=telanova-support,env=production" \
  --project "${PROJECT_ID}"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

echo ""
echo "=== Deployment Complete ==="
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: ${SERVICE_URL}/health"
echo "Chat Endpoint: ${SERVICE_URL}/chat"
echo "Webhook URL (for Dialogflow CX): ${SERVICE_URL}/webhook"
echo ""
echo "Next Steps:"
echo "1. Update your Dialogflow CX webhook URL to: ${SERVICE_URL}/webhook"
echo "2. Test the health endpoint: curl ${SERVICE_URL}/health"
echo "3. Test a chat message:"
echo "   curl -X POST ${SERVICE_URL}/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Why is my bill high this month?\"}'"
