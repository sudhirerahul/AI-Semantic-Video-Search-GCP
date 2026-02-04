#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0067393875"
REGION="us-central1"
IMAGE_REPO="us-central1-docker.pkg.dev/gen-lang-client-0067393875/video-search-repo"
IMAGE_NAME="ingest-worker"
SERVICE_NAME="video-ingest-worker"
SERVICE_ACCOUNT="video-search-sa@gen-lang-client-0067393875.iam.gserviceaccount.com"

echo "🏗️  Building Docker image..."

# Build and push image
docker build -t ${IMAGE_REPO}/${IMAGE_NAME}:latest .

echo "📤 Pushing image to Artifact Registry..."
docker push ${IMAGE_REPO}/${IMAGE_NAME}:latest

echo "🚀 Deploying to Cloud Run..."

gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_REPO}/${IMAGE_NAME}:latest \
  --platform=managed \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=4Gi \
  --cpu=2 \
  --timeout=600 \
  --max-instances=3 \
  --min-instances=0 \
  --no-allow-unauthenticated \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},BUCKET_NAME=gen-lang-client-0067393875-media-1770102442"

echo "✅ Deployment complete!"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(status.url)')

echo ""
echo "📍 Service URL: ${SERVICE_URL}"
echo ""
echo "Next step: Configure Pub/Sub push subscription"
echo "Run: ./configure_pubsub.sh"
