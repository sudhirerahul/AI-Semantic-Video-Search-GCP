#!/bin/bash

# Simple Backend Starter
# Run this in your terminal (not in background)

cd "$(dirname "$0")"

echo "Starting Cloud Clip API..."
echo "This will run in foreground. Press Ctrl+C to stop."
echo ""

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/video-search-sa-key.json"

# Run in foreground
exec worker/venv/bin/python search-api/cloud_clip_api.py
