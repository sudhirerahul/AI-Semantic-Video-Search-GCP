#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0067393875"
REGION="us-central1"
IMAGE_REPO="us-central1-docker.pkg.dev/gen-lang-client-0067393875/video-search-repo"
IMAGE_NAME="video-search-api"
SERVICE_NAME="video-search-api"
SERVICE_ACCOUNT="video-search-sa@gen-lang-client-0067393875.iam.gserviceaccount.com"

# Check if FAISS index exists
if [ ! -f "./faiss_index/video_chunks.faiss" ]; then
    echo "❌ FAISS index not found. Run ./build_index.sh first."
    exit 1
fi

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
  --memory=2Gi \
  --cpu=1 \
  --timeout=60 \
  --max-instances=5 \
  --min-instances=0 \
  --allow-unauthenticated \
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
echo "🧪 Test the API:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo '  curl -X POST '"${SERVICE_URL}"'/search -H "Content-Type: application/json" -d '"'"'{"query": "person walking", "top_k": 5}'"'"' | jq .'
