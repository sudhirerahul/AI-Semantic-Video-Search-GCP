#!/bin/bash

# Start Cloud Clip Extraction System
# Uses pre-uploaded videos from GCS, no manual upload needed

set -e

PROJECT_ROOT="/Users/sudhirerahul/Desktop/GCP_Media_proto"

echo "Starting Cloud Clip Extraction System"
echo ""

# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_ROOT/video-search-sa-key.json"

# Kill existing processes
killall -9 python 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start Backend API with credentials
echo "Starting Cloud Clip API (port 8080)..."
cd "$PROJECT_ROOT"
GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_ROOT/video-search-sa-key.json" \
  "$PROJECT_ROOT/worker/venv/bin/python" search-api/cloud_clip_api.py > /tmp/cloud_clip_api.log 2>&1 &
API_PID=$!
echo "Waiting for API to initialize (loading CLIP model)..."
sleep 10

# Check API health
if curl -s http://localhost:8080/health > /dev/null; then
    echo "Backend API running (PID: $API_PID)"
else
    echo "Backend API failed to start"
    echo "Check logs: tail -f /tmp/cloud_clip_api.log"
    exit 1
fi

# Start Frontend UI
echo "Starting Frontend UI (port 8000)..."
python3 -m http.server 8000 > /tmp/cloud_clip_ui.log 2>&1 &
UI_PID=$!
sleep 2

echo ""
echo "All services running"
echo ""
echo "Open in browser: http://localhost:8000/cloud-clip-ui.html"
echo "API endpoint: http://localhost:8080"
echo ""
echo "Stop services: kill $API_PID $UI_PID"
echo ""
echo "Features:"
echo "  - Pre-uploaded videos from GCS"
echo "  - Natural language scene search"
echo "  - On-demand clip extraction"
echo "  - No manual upload required"
echo "  - Inter font, no emojis"
