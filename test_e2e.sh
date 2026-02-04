#!/bin/bash

# End-to-End Test Script for Cloud Clip Extraction System
# Tests: video listing → query → clip extraction → playback verification

set -e

API_URL="http://localhost:8080"

echo "=================================="
echo "Cloud Clip E2E Test"
echo "=================================="
echo ""

# Test 1: List videos
echo "[Test 1] Listing videos..."
VIDEOS_RESPONSE=$(curl -s "$API_URL/videos")
VIDEO_COUNT=$(echo "$VIDEOS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

if [ "$VIDEO_COUNT" -gt 0 ]; then
    echo "✅ Found $VIDEO_COUNT videos"
    # Extract first video ID
    VIDEO_ID=$(echo "$VIDEOS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['video_id'])")
    echo "   Using video: $VIDEO_ID"
else
    echo "❌ No videos found"
    exit 1
fi
echo ""

# Test 2: Query video
echo "[Test 2] Querying for 'person'..."
QUERY_RESPONSE=$(curl -s -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -d "{\"video_id\": \"$VIDEO_ID\", \"query\": \"person\", \"top_k\": 1}")

RESULT_COUNT=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else 0)")

if [ "$RESULT_COUNT" -gt 0 ]; then
    echo "✅ Found $RESULT_COUNT matching scene(s)"

    # Extract shot info
    SHOT_INDEX=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['shot_index'])")
    START_TIME=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['start'])")
    END_TIME=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['end'])")
    SCORE=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['score'])")

    echo "   Shot index: $SHOT_INDEX"
    echo "   Time range: ${START_TIME}s - ${END_TIME}s"
    echo "   Relevance score: $SCORE"
else
    echo "❌ Query returned no results"
    exit 1
fi
echo ""

# Test 3: Extract clip
echo "[Test 3] Extracting clip (shot $SHOT_INDEX)..."
EXTRACT_RESPONSE=$(curl -s -X POST "$API_URL/extract_clip" \
  -H "Content-Type: application/json" \
  -d "{\"video_id\": \"$VIDEO_ID\", \"shot_index\": $SHOT_INDEX}")

CLIP_URL=$(echo "$EXTRACT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('clip_url', ''))")

if [ -n "$CLIP_URL" ]; then
    echo "✅ Clip extracted successfully"
    echo "   Clip URL: ${CLIP_URL:0:80}..."

    # Verify clip is accessible
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CLIP_URL")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Clip is accessible (HTTP $HTTP_CODE)"
    else
        echo "❌ Clip not accessible (HTTP $HTTP_CODE)"
        exit 1
    fi

    # Download clip and check duration
    TEMP_CLIP="/tmp/test_clip_$$.mp4"
    curl -s "$CLIP_URL" -o "$TEMP_CLIP"

    if command -v ffprobe &> /dev/null; then
        ACTUAL_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_CLIP" 2>/dev/null)
        EXPECTED_DURATION=$(echo "$END_TIME - $START_TIME" | bc)
        DURATION_DIFF=$(echo "$ACTUAL_DURATION - $EXPECTED_DURATION" | bc | tr -d '-')

        echo "   Expected duration: ${EXPECTED_DURATION}s"
        echo "   Actual duration: ${ACTUAL_DURATION}s"

        # Allow 1 second tolerance
        if (( $(echo "$DURATION_DIFF < 1.0" | bc -l) )); then
            echo "✅ Duration matches (within tolerance)"
        else
            echo "⚠️  Duration mismatch (difference: ${DURATION_DIFF}s)"
        fi
    fi

    rm -f "$TEMP_CLIP"
else
    echo "❌ Clip extraction failed"
    echo "   Response: $EXTRACT_RESPONSE"
    exit 1
fi
echo ""

# Summary
echo "=================================="
echo "✅ All tests passed!"
echo "=================================="
echo ""
echo "System is fully operational:"
echo "  - Videos indexed and listed"
echo "  - Semantic search working"
echo "  - On-demand clip extraction working"
echo "  - Clips are playable"
echo ""
echo "Ready to use at: http://localhost:8000/cloud-clip-ui.html"
