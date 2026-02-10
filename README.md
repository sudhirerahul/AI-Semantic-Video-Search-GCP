# AI Video Search

Semantic video search with natural language queries, powered by CLIP embeddings and Gemini 2.0 Flash.

## Architecture

**Frontend**: Next.js 14 (React 18) + TailwindCSS + SWR
**Backend**: Python 3.11 + Flask + CLIP ViT-B-32 + Gemini 2.0 Flash
**Infrastructure**: Google Cloud Platform (GCP)
**Deployment**: Netlify (frontend) + Cloud Run (backend)

## Live Application

- **Frontend**: https://gcp-media-pro.netlify.app
- **Backend API**: https://cloud-clip-api-107631450464.us-central1.run.app

## GCP Products & SDK Used

### Core Services

**1. Cloud Run** - Serverless container platform hosting the Flask API
- Auto-scaling (0-10 instances)
- 2Gi memory, 2 CPU, 300s timeout
- Region: us-central1
- SDK: `gcloud run deploy`

**2. Cloud Storage (GCS)** - Object storage for videos, indexes, and clips
- Bucket: `gen-lang-client-0067393875-media-1770102442`
- Lifecycle policy: Auto-delete clips after 1 day
- Public read access for thumbnails/clips
- SDK: `google-cloud-storage` Python library

**3. Cloud Build** - CI/CD for Docker image builds
- Builds from GitHub repository
- Pushes to Container Registry
- SDK: `gcloud builds submit`

**4. Container Registry (GCR)** - Docker image storage
- Image: `gcr.io/gen-lang-client-0067393875/cloud-clip-api`

**5. Vertex AI / Gemini API** - AI-powered query enhancement
- Model: Gemini 2.0 Flash
- Expands user queries with synonyms and variations
- SDK: `google-generativeai` Python library

### Supporting Services
- **IAM & Service Accounts** - Authentication and authorization
- **Cloud Logging** - Application logs and request traces
- **Workload Identity** - Secure Cloud Run to GCS authentication

### GCS Bucket Structure
```
gs://gen-lang-client-0067393875-media-1770102442/
├── videos/              # Source videos (permanent)
├── index/               # CLIP embeddings + metadata (permanent)
│   └── {video_id}/
│       ├── shots.json
│       ├── embeddings.json
│       └── thumbs/
└── extracts/            # Generated clips (1-day TTL)
```

## How It Works

### 1. Video Indexing (Offline)
Videos are batch-processed using `worker/video_indexer.py`:
- FFmpeg detects scene changes (threshold=0.3)
- Extracts thumbnail for each shot (middle frame)
- Generates 512-dim CLIP embeddings for each thumbnail
- Stores index in GCS: `index/{video_id}/`

### 2. Search (Runtime)
User enters natural language query:
- **Gemini 2.0 Flash** expands query with synonyms
- Query encoded with CLIP ViT-B-32
- Cosine similarity search against video embeddings
- Returns top K matching shots with thumbnails

### 3. Clip Extraction (On-Demand)
User clicks "Play" on a result:
- API downloads source video from GCS
- **FFmpeg** extracts precise clip (`-ss START -t DURATION -c copy`)
- Uploads clip to `extracts/` with 1-day lifecycle
- Returns public GCS URL
- Auto-cleanup prevents storage accumulation

## Technology Stack

### Backend (`search-api/`)
```
Flask 3.0               # REST API framework
Flask-CORS              # Cross-origin resource sharing
google-cloud-storage    # GCS SDK for Python
google-generativeai     # Gemini 2.0 Flash SDK
sentence-transformers   # CLIP ViT-B-32 embeddings
torch                   # PyTorch ML framework
numpy                   # Vector operations
gunicorn                # Production WSGI server
FFmpeg                  # Video processing (system package)
```

### Frontend (`frontend/`)
```
Next.js 14              # React framework
React 18                # UI library
TailwindCSS 3.4         # Utility-first CSS
SWR 2.2.5               # Data fetching & caching
Inter font              # Typography (Google Fonts)
```

### Design System
- **Color**: Control-console aesthetic (charcoal `#0D0E11`, indigo accents `#6366F1`)
- **Typography**: Inter font, tight spacing, 13-15px sizes
- **Theme**: Dark mode, precise tab underlines, no decorative elements
- **Philosophy**: Operational states, not playful navigation

## API Endpoints

### `GET /videos`
List all indexed videos with metadata.

**Response:**
```json
[
  {
    "video_id": "videoplayback_1_d2078ef2",
    "title": "Videoplayback 1",
    "num_shots": 39,
    "duration": 235.9,
    "poster_thumbnail_url": "https://storage.googleapis.com/...",
    "indexed_at": "2026-02-03T22:59:38Z"
  }
]
```

### `POST /query`
Search for scenes using natural language (enhanced by Gemini).

**Request:**
```json
{
  "video_id": "videoplayback_1_d2078ef2",
  "query": "person speaking",
  "top_k": 3
}
```

**Response:**
```json
[
  {
    "shot_index": 32,
    "start": 196.32,
    "end": 200.16,
    "thumbnail_url": "https://storage.googleapis.com/...",
    "score": 0.87
  }
]
```

### `POST /extract_clip`
Extract clip on-demand from GCS video.

**Request:**
```json
{
  "video_id": "videoplayback_1_d2078ef2",
  "shot_index": 32
}
```

**Response:**
```json
{
  "clip_url": "https://storage.googleapis.com/...",
  "start": 196.32,
  "end": 200.16,
  "duration": 3.84,
  "expires_at": "2026-02-03T23:59:00Z"
}
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg installed
- GCP credentials configured

### Backend Setup
```bash
cd search-api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

export PROJECT_ID=gen-lang-client-0067393875
export BUCKET_NAME=gen-lang-client-0067393875-media-1770102442
export GEMINI_API_KEY=your-api-key  # Optional

python cloud_clip_api.py
# API runs on http://localhost:8080
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# UI runs on http://localhost:3000
```

### Index New Videos
```bash
cd worker
source venv/bin/activate
python video_indexer.py
```

## Deployment

### Backend (Cloud Run)
```bash
cd /path/to/GCP_Media_proto
./deploy_to_cloud_run.sh
```

Or manually:
```bash
cd search-api
gcloud builds submit --tag gcr.io/gen-lang-client-0067393875/cloud-clip-api
gcloud run deploy cloud-clip-api \
  --image gcr.io/gen-lang-client-0067393875/cloud-clip-api \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

### Frontend (Netlify)
Automatic deployment on git push to `main` branch.

Configuration in `netlify.toml`:
- Build command: `npm run build`
- Publish directory: `out`
- Base directory: `frontend`

## Performance

| Operation | Target | Actual |
|-----------|--------|--------|
| Query latency | <5s | <500ms |
| Clip extraction | <20s | 10-20s |
| Video indexing | <5min | 2-3min |

## Cost Estimates

### Storage (100 videos)
- Videos (15MB avg): ~1.5GB = $0.023/month
- Index files: ~50MB = $0.001/month
- Thumbnails: ~500MB = $0.008/month

**Total**: ~$0.03/month

### Compute (1000 queries/month)
- Cloud Run: $0.00 (free tier)
- Netlify: $0.00 (free tier)
- Clip extractions: ~$0.05

**Total**: ~$0.05/month

### Production Scale (10K queries/month)
- Storage: ~$0.50/month
- Compute: ~$2-3/month
- Networking: ~$0.20/month

**Total**: ~$3-5/month

## Project Structure

```
GCP_Media_proto/
├── frontend/                    # Next.js application
│   ├── app/                     # Next.js App Router
│   ├── components/              # React components
│   ├── lib/                     # API client
│   └── public/                  # Static assets
│
├── search-api/                  # Flask backend
│   ├── cloud_clip_api.py        # Main API (CLIP + Gemini)
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container definition
│   └── cloudbuild.yaml          # Cloud Build config
│
├── worker/                      # Video indexing
│   ├── video_indexer.py         # FFmpeg + CLIP indexer
│   └── venv/                    # Python virtual environment
│
├── netlify.toml                 # Netlify configuration
├── deploy_to_cloud_run.sh       # Backend deployment script
└── README.md                    # This file
```

## Security

### Implemented
- Service account authentication (Cloud Run ↔ GCS)
- CORS enabled for Netlify domain
- Public GCS URLs (bucket is publicly readable)
- Input validation on all endpoints
- Auto-expiring clips (1-day lifecycle)

### Production Recommendations
- Add user authentication (OAuth, Auth0)
- Rate limiting (10 requests/min per IP)
- Cloud Armor for DDoS protection
- Private GCS bucket with signed URLs
- Budget alerts at $100/month
- Content Security Policy headers

## Adding New Videos

1. Upload to GCS:
```bash
gsutil cp new_video.mp4 gs://BUCKET_NAME/videos/
```

2. Index the video:
```bash
cd worker
source venv/bin/activate
python video_indexer.py
```

3. Refresh the UI to see the new video

## Troubleshooting

### Videos not loading
Check backend CORS configuration and Cloud Run logs:
```bash
gcloud run services logs read cloud-clip-api --region us-central1 --limit 50
```

### Clip extraction fails
Verify FFmpeg is installed in Cloud Run container:
```bash
gcloud run services describe cloud-clip-api --region us-central1
```

### Query returns no results
Check if video is indexed:
```bash
gsutil ls gs://BUCKET_NAME/index/
```

## License

MIT
