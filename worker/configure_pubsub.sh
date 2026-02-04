#!/bin/bash
set -e

PROJECT_ID="gen-lang-client-0067393875"
REGION="us-central1"
SERVICE_NAME="video-ingest-worker"
TOPIC_NAME="video-upload-events"
SUBSCRIPTION_NAME="video-processing-sub"
SERVICE_ACCOUNT="video-search-sa@gen-lang-client-0067393875.iam.gserviceaccount.com"

echo "🔧 Configuring Pub/Sub push subscription..."

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(status.url)')

echo "📍 Cloud Run service URL: ${SERVICE_URL}"

# Grant Pub/Sub permission to invoke Cloud Run
echo "🔐 Granting Pub/Sub invoker permission..."

gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --member="serviceAccount:service-107631450464@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=${REGION} \
  --project=${PROJECT_ID}

# Update subscription to push mode
echo "📨 Updating Pub/Sub subscription to push mode..."

gcloud pubsub subscriptions update ${SUBSCRIPTION_NAME} \
  --push-endpoint="${SERVICE_URL}/" \
  --project=${PROJECT_ID}

echo ""
echo "✅ Pub/Sub configuration complete!"
echo ""
echo "🧪 Test the pipeline:"
echo "   python ../trigger/trigger_processing.py gs://gen-lang-client-0067393875-media-1770102442/raw/sample_video.mp4"
