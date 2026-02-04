#!/bin/bash

# Smoke Test Script for GCP Media Frontend
# Tests deployment health and basic functionality

set -e

FRONTEND_URL="${1:-http://localhost:3000}"
API_BASE="${2:-http://localhost:8080}"

echo "=========================================="
echo "GCP Media Frontend - Smoke Tests"
echo "=========================================="
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo "API Base: $API_BASE"
echo ""

# Test 1: Homepage loads
echo "[Test 1] Testing homepage accessibility..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Homepage loads (HTTP $HTTP_CODE)"
else
    echo "❌ Homepage failed (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# Test 2: API endpoint configured
echo "[Test 2] Checking API configuration..."
PAGE_CONTENT=$(curl -s "$FRONTEND_URL")

if echo "$PAGE_CONTENT" | grep -q "GCP Media"; then
    echo "✅ Page content loads correctly"
else
    echo "❌ Page content missing or malformed"
    exit 1
fi
echo ""

# Test 3: Backend API health
echo "[Test 3] Testing backend API health..."
API_HEALTH=$(curl -s "$API_BASE/health" || echo "failed")

if echo "$API_HEALTH" | grep -q "healthy"; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️  Backend API not responding (expected if testing frontend only)"
fi
echo ""

# Test 4: Videos endpoint
echo "[Test 4] Testing /videos endpoint..."
VIDEOS_RESPONSE=$(curl -s "$API_BASE/videos" || echo "failed")

if echo "$VIDEOS_RESPONSE" | grep -q '\['; then
    VIDEO_COUNT=$(echo "$VIDEOS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "✅ Videos endpoint responds ($VIDEO_COUNT videos found)"
else
    echo "⚠️  Videos endpoint not responding (expected if testing frontend only)"
fi
echo ""

# Test 5: Query endpoint (if videos exist)
if [ "$VIDEO_COUNT" -gt 0 ]; then
    echo "[Test 5] Testing /query endpoint..."
    VIDEO_ID=$(echo "$VIDEOS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['video_id'])" 2>/dev/null)

    QUERY_RESPONSE=$(curl -s -X POST "$API_BASE/query" \
        -H "Content-Type: application/json" \
        -d "{\"video_id\": \"$VIDEO_ID\", \"query\": \"test\", \"top_k\": 1}" || echo "failed")

    if echo "$QUERY_RESPONSE" | grep -q '\['; then
        echo "✅ Query endpoint responds"
    else
        echo "⚠️  Query endpoint not responding"
    fi
    echo ""

    # Test 6: Clip extraction endpoint
    echo "[Test 6] Testing /extract_clip endpoint (metadata only)..."
    EXTRACT_RESPONSE=$(curl -s -X POST "$API_BASE/extract_clip" \
        -H "Content-Type: application/json" \
        -d "{\"video_id\": \"$VIDEO_ID\", \"shot_index\": 0}" || echo "failed")

    if echo "$EXTRACT_RESPONSE" | grep -q 'clip_url'; then
        echo "✅ Clip extraction endpoint responds"
    else
        echo "⚠️  Clip extraction endpoint not responding"
    fi
    echo ""
fi

# Test 7: Check for common issues
echo "[Test 7] Checking for common issues..."

# Check if API_BASE is hardcoded to localhost in production
if [ "$FRONTEND_URL" != "http://localhost:3000" ]; then
    PAGE_SOURCE=$(curl -s "$FRONTEND_URL")
    if echo "$PAGE_SOURCE" | grep -q "localhost:8080"; then
        echo "⚠️  WARNING: Frontend may be using hardcoded localhost API"
        echo "   Verify NEXT_PUBLIC_API_BASE environment variable"
    else
        echo "✅ No hardcoded localhost references found"
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "Smoke Test Summary"
echo "=========================================="
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ All critical tests passed!"
    echo ""
    echo "Frontend is accessible at: $FRONTEND_URL"

    if [ "$VIDEO_COUNT" -gt 0 ]; then
        echo "Backend is operational with $VIDEO_COUNT indexed videos"
    fi

    echo ""
    echo "Next steps:"
    echo "1. Open $FRONTEND_URL in browser"
    echo "2. Select a video from the left panel"
    echo "3. Enter a search query (e.g., 'person speaking')"
    echo "4. Click Play on a scene card"
    echo "5. Verify video plays in right panel"
else
    echo "❌ Tests failed - check logs above"
    exit 1
fi

echo ""
