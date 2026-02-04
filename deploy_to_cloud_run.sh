#!/bin/bash

# Deploy Cloud Clip API to Cloud Run with Gemini integration

set -e

PROJECT_ID="gen-lang-client-0067393875"
BUCKET_NAME="gen-lang-client-0067393875-media-1770102442"
SERVICE_NAME="cloud-clip-api"
REGION="us-central1"
SERVICE_ACCOUNT="video-search-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Deploying Cloud Clip API to Cloud Run"
echo "=========================================="
echo ""

# Step 1: Build and push Docker image
echo "[1/3] Building Docker image..."
cd search-api
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Step 2: Deploy to Cloud Run
echo ""
echo "[2/3] Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 10 \
  --min-instances 0 \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars PROJECT_ID=${PROJECT_ID},BUCKET_NAME=${BUCKET_NAME}

# Step 3: Get service URL
echo ""
echo "[3/3] Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test endpoints:"
echo "  Health: ${SERVICE_URL}/health"
echo "  Videos: ${SERVICE_URL}/videos"
echo ""
echo "Next steps:"
echo "1. Test the API: curl ${SERVICE_URL}/health"
echo "2. Deploy frontend to Vercel with this API URL"
echo ""
