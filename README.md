# Cloud Clip Extraction - AI Video Scene Search

> Semantic video search with on-demand clip extraction from cloud-stored videos. No manual upload - videos are pre-indexed in GCS.

---

## Quick Start

```bash
# Start the system
./start_cloud_clip.sh

# Open browser
open http://localhost:8000/cloud-clip-ui.html
```

That's it! Select a video, enter a query like "person speaking", and watch clips get extracted on demand.

---

## Features

- **No Upload UI** - Videos pre-uploaded to GCS, indexed offline
- **Natural Language Search** - Find scenes using plain English queries
- **On-Demand Clip Extraction** - Clips generated only when requested
- **Fast Performance** - Query < 500ms, clip extraction 10-20s
- **Auto-Cleanup** - Clips deleted after 1 day (GCS lifecycle)
- **Clean UI** - Inter font, no emojis, dark aesthetic

---

## Architecture

```
Videos in GCS (gs://bucket/videos/)
    ↓ Indexed offline (FFmpeg + CLIP)
    ↓
Index stored (gs://bucket/index/)
    ↓
User queries "person speaking"
    ↓ CLIP embedding + vector search
    ↓
Top scenes returned with thumbnails
    ↓
User clicks "Play clip"
    ↓ FFmpeg extracts clip on-demand
    ↓
Clip uploaded to GCS with signed URL
    ↓
Browser plays clip (auto-deleted in 1 day)
```

---

## API Endpoints

### GET /videos
List all indexed videos with metadata.

### POST /query
Search for scenes using natural language.

**Request:**
```json
{
  "video_id": "videoplayback_1_d2078ef2",
  "query": "person speaking",
  "top_k": 5
}
```

### POST /extract_clip
Extract clip on-demand from cloud video.

**Request:**
```json
{
  "video_id": "videoplayback_1_d2078ef2",
  "shot_index": 5
}
```

---

## Adding New Videos

### 1. Upload to GCS
```bash
gsutil cp my_video.mp4 gs://<BUCKET>/videos/
```

### 2. Index the video
```bash
cd worker
./venv/bin/python video_indexer.py \
  --project-id <PROJECT_ID> \
  --bucket-name <BUCKET_NAME> \
  --video-path gs://<BUCKET>/videos/my_video.mp4
```

### 3. Refresh UI
Videos appear automatically in the selector.

---

## Testing

### Run End-to-End Tests
```bash
./test_e2e.sh
```

Tests:
- Video listing
- Semantic search
- Clip extraction
- Duration verification

### Manual Testing
```bash
# List videos
curl http://localhost:8080/videos | jq

# Search
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"video_id": "videoplayback_1_d2078ef2", "query": "person", "top_k": 3}' | jq

# Extract clip
curl -X POST http://localhost:8080/extract_clip \
  -H "Content-Type: application/json" \
  -d '{"video_id": "videoplayback_1_d2078ef2", "shot_index": 5}' | jq
```

---

## Performance

- **Indexing**: 2-3 min per 5-min video
- **Query**: < 500ms
- **Clip extraction**: 10-20s
- **Accuracy**: 20-30% scores are relevant

---

## Cost

### Storage (per 100 videos)
- Videos: ~$0.023/month
- Index files: ~$0.001/month
- Thumbnails: ~$0.008/month
- **Total**: ~$0.032/month

### Operations (per 1000 queries)
- Queries: $0.00 (free tier)
- Clip extractions (100): ~$0.05
- **Total**: ~$0.05 per 1000 queries

**Auto-cleanup saves $0.50/month per 1000 clips**

---

## Project Structure

```
GCP_Media_proto/
├── README.md                    # This file
├── CLOUD_CLIP_README.md         # Complete documentation
├── IMPLEMENTATION_SUMMARY.md    # Technical details
├── SYSTEM_READY.md              # Quick reference
│
├── cloud-clip-ui.html           # Frontend (Inter font, no emojis)
├── start_cloud_clip.sh          # Startup script
├── test_e2e.sh                  # End-to-end tests
├── lifecycle-config.json        # GCS auto-cleanup rules
│
├── search-api/
│   └── cloud_clip_api.py        # Flask API with 3 endpoints
│
├── worker/
│   └── video_indexer.py         # Offline indexing system
│
└── videos/                      # Local videos (uploaded to GCS)
```

---

## Documentation

- **CLOUD_CLIP_README.md** - Complete documentation (400+ lines)
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details
- **SYSTEM_READY.md** - Quick start guide and system status

---

## Requirements

- Python 3.11+
- FFmpeg
- GCP project with service account
- GCS bucket

---

## Troubleshooting

### Videos not appearing
```bash
# Check if indexed
gsutil ls gs://<BUCKET>/index/

# Re-index all videos
cd worker
./venv/bin/python video_indexer.py --project-id <PROJECT_ID> --bucket-name <BUCKET_NAME>
```

### Query returns no results
Try broader queries:
- ❌ "person in red shirt holding coffee"
- ✅ "person"

### Clip extraction fails
```bash
# Check FFmpeg
ffmpeg -version

# Check logs
tail -f /tmp/cloud_clip_api.log
```

---

## Tech Stack

- **Frontend**: HTML + Tailwind CSS + Inter font
- **Backend**: Flask + Python
- **Video**: FFmpeg (scene detection + extraction)
- **AI**: CLIP ViT-B-32 (semantic embeddings)
- **Search**: NumPy cosine similarity
- **Storage**: Google Cloud Storage
- **Security**: Signed URLs (60-min expiry)

---

## Credits

Built with CLIP (OpenAI), FFmpeg, Flask, and Google Cloud Platform.

---

## License

Prototype for demonstration purposes.

---

**Ready to use**: `./start_cloud_clip.sh` then open http://localhost:8000/cloud-clip-ui.html
