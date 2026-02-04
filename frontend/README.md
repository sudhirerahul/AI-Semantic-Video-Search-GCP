# GCP Media Frontend - Next.js Chat UI

Production-ready Next.js frontend for cloud clip extraction system, mimicking OpenAI's chat interface.

## Features

- OpenAI-style chat UI with left history panel, center chat area, right video player
- Inter font globally, no emojis anywhere
- Dark theme matching Perplexity Comet aesthetic
- Real-time video scene search with CLIP embeddings
- On-demand clip extraction and playback
- Query history persistence (localStorage)
- Responsive design with smooth animations

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                         Header                              │
├──────────────┬─────────────────────────┬───────────────────┤
│              │                         │                   │
│   History    │      Chat Area          │   Video Player    │
│   Panel      │                         │   Panel           │
│   (270px)    │      (flexible)         │   (420px)         │
│              │                         │                   │
│  - Videos    │  - Messages             │  - Clip playback  │
│  - History   │  - Query input          │  - Metadata       │
│              │  - Scene cards          │  - Download       │
│              │                         │                   │
└──────────────┴─────────────────────────┴───────────────────┘
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI**: React 18, TailwindCSS 3.4
- **Data Fetching**: SWR 2.2.5
- **Fonts**: Inter (Google Fonts)
- **Deployment**: Vercel

## Local Development

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see main README)

### Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Create `.env.local`:**
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

3. **Start dev server:**
```bash
npm run dev
```

Opens at: http://localhost:3000

### Development Commands

```bash
npm run dev      # Start dev server (port 3000)
npm run build    # Production build
npm run start    # Start production server
```

## Vercel Deployment

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/gcp-media-proto/tree/main/frontend)

### Manual Deployment

#### Step 1: Push to GitHub

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto
git init
git add .
git commit -m "Initial commit: Next.js frontend + GCP backend"
git branch -M main
git remote add origin https://github.com/yourusername/gcp-media-proto.git
git push -u origin main
```

#### Step 2: Deploy Backend API to Cloud Run

```bash
# Build and deploy backend
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Create Dockerfile for backend
cat > search-api/Dockerfile <<'EOF'
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY cloud_clip_api.py /app/
WORKDIR /app

CMD ["python", "cloud_clip_api.py"]
EOF

# Deploy to Cloud Run
cd search-api
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cloud-clip-api
gcloud run deploy cloud-clip-api \
  --image gcr.io/YOUR_PROJECT_ID/cloud-clip-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 300s \
  --allow-unauthenticated \
  --service-account video-search-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,BUCKET_NAME=YOUR_BUCKET_NAME

# Note the service URL (e.g., https://cloud-clip-api-xxxxx-uc.a.run.app)
```

#### Step 3: Deploy Frontend to Vercel

1. **Go to [vercel.com](https://vercel.com) and sign in**

2. **Click "Add New Project"**

3. **Import your GitHub repository:**
   - Select `gcp-media-proto` repository
   - Set root directory to `frontend`

4. **Configure project:**
   - Framework Preset: Next.js
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)
   - Install Command: `npm install` (auto-detected)

5. **Add environment variable:**
   - Key: `NEXT_PUBLIC_API_BASE`
   - Value: `https://cloud-clip-api-xxxxx-uc.a.run.app` (your Cloud Run URL)

6. **Click "Deploy"**

Deployment takes ~2 minutes. You'll get a URL like: `https://gcp-media-frontend.vercel.app`

#### Step 4: Enable CORS on Backend

Update `search-api/cloud_clip_api.py`:

```python
# Add Vercel domain to CORS
CORS(app, origins=[
    'http://localhost:3000',
    'https://gcp-media-frontend.vercel.app',  # Add your Vercel domain
    'https://*.vercel.app',  # Allow all preview deployments
])
```

Redeploy backend:
```bash
cd search-api
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cloud-clip-api
gcloud run deploy cloud-clip-api --image gcr.io/YOUR_PROJECT_ID/cloud-clip-api
```

### Custom Domain (Optional)

1. **In Vercel project settings:**
   - Go to Settings > Domains
   - Add your custom domain (e.g., `clips.yourdomain.com`)
   - Follow DNS configuration instructions

2. **Update backend CORS:**
   - Add custom domain to CORS origins
   - Redeploy backend

## Environment Variables

### Local Development (`.env.local`)

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

### Production (Vercel)

Set in Vercel dashboard under Settings > Environment Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_BASE` | `https://your-api.run.app` | Backend API base URL (Cloud Run) |

## Smoke Tests

Run automated smoke tests after deployment:

```bash
cd frontend
chmod +x scripts/smoke_test.sh
./scripts/smoke_test.sh https://gcp-media-frontend.vercel.app
```

Expected output:
```
Testing GCP Media Frontend at https://gcp-media-frontend.vercel.app
✅ Homepage loads (HTTP 200)
✅ API endpoint configured correctly
✅ Videos endpoint responds
✅ Query endpoint responds
✅ Clip extraction endpoint responds
✅ All tests passed!
```

## UI Components

### Header (`components/Header.jsx`)
- Top navigation bar with branding
- 60px height with border-bottom

### LeftHistoryPanel (`components/LeftHistoryPanel.jsx`)
- 270px width sidebar
- Video selector with thumbnails
- History list with timestamps
- "New conversation" button

### ChatArea (`components/ChatArea.jsx`)
- Flexible center panel
- Message history (user/assistant)
- Query input with submit button
- Scene cards with Play buttons

### SceneCard (`components/SceneCard.jsx`)
- Thumbnail preview
- Time range and score badge
- Play button with loading state
- Error handling

### VideoPlayerPanel (`components/VideoPlayerPanel.jsx`)
- 420px width right panel
- HTML5 video player with controls
- Expiry countdown notice
- Download and "Open in tab" links
- Metadata display

## API Integration

All API calls go through `lib/api.js`:

```javascript
import { getVideos, queryScenes, extractClip } from '@/lib/api'

// List indexed videos
const videos = await getVideos()

// Search for scenes
const scenes = await queryScenes(video_id, "person speaking", 3)

// Extract clip (45s timeout)
const clip = await extractClip(video_id, shot_index)
```

### Error Handling

API wrapper includes:
- Network timeout handling (20s default, 45s for extraction)
- Automatic JSON parsing
- Descriptive error messages
- Retry logic not needed (backend is idempotent)

## Styling

### Theme Colors

```javascript
// tailwind.config.js
colors: {
  brand: {
    dark: '#0B0F14',           // Background
    surface: '#0E1216',        // Cards
    border: 'rgba(255,255,255,0.06)',
    text: {
      primary: '#ECECF1',      // Main text
      secondary: '#9B9CA3',    // Secondary text
      tertiary: '#6E6F73',     // Muted text
    },
    accent: {
      primary: '#7C3AED',      // Purple
      hover: '#8B5CF6',
    }
  }
}
```

### Typography

- Font: Inter (Google Fonts)
- Weights: 300, 400, 600, 700
- No emojis anywhere (plain Unicode only)

### Animations

```css
/* Fade-in for new elements */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Pulse for loading states */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Performance Optimizations

- SWR for automatic caching and revalidation
- Next.js Image optimization (disabled for GCS URLs)
- LocalStorage for history persistence
- Debounced query input (not implemented - can be added)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires:
- HTML5 video support
- LocalStorage API
- Fetch API
- ES6+ JavaScript

## Troubleshooting

### "Failed to fetch videos"

**Check backend API:**
```bash
curl https://your-api.run.app/videos
```

**Verify CORS configuration:**
- Ensure Vercel domain is in backend CORS origins
- Check browser console for CORS errors

### "Failed to extract clip"

**Check backend logs:**
```bash
gcloud run logs read cloud-clip-api --limit 50
```

**Common causes:**
- Video not indexed (run video_indexer.py)
- FFmpeg timeout (increase Cloud Run timeout)
- GCS permissions (check service account)

### Videos not displaying

**Check API_BASE environment variable:**
```bash
# In Vercel dashboard
Settings > Environment Variables > NEXT_PUBLIC_API_BASE
```

**Verify signed URLs:**
- URLs expire after 60 minutes
- Check GCS bucket permissions

### History not persisting

**Check localStorage:**
```javascript
// In browser console
console.log(localStorage.getItem('query_history'))
```

**Clear history:**
```javascript
localStorage.removeItem('query_history')
```

## Cost Estimates

### Vercel Hosting

**Free Tier (Hobby):**
- 100 GB bandwidth/month
- Unlimited deployments
- Serverless functions (10s timeout)

**Pro Tier ($20/month):**
- 1 TB bandwidth/month
- Analytics included
- 60s function timeout

### Typical Usage (1000 queries/month)

- Frontend hosting: $0 (free tier)
- Backend API: $0.05 (Cloud Run)
- GCS operations: $0.05
- **Total: ~$0.10/month**

### High Traffic (10K queries/month)

- Frontend hosting: $20 (Pro tier)
- Backend API: $5 (Cloud Run)
- GCS operations: $0.50
- **Total: ~$25.50/month**

## Security

### API Authentication

- Backend uses service account for GCS
- No authentication required for frontend (public demo)
- For production: Add OAuth or API keys

### Content Security Policy

Add to `next.config.js`:
```javascript
async headers() {
  return [
    {
      source: '/:path*',
      headers: [
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; img-src 'self' https://storage.googleapis.com; media-src https://storage.googleapis.com; font-src 'self' https://fonts.gstatic.com;"
        }
      ]
    }
  ]
}
```

### Environment Variables

- Never commit `.env.local` to git
- Use Vercel environment variables for production
- Rotate GCS service account keys regularly

## Monitoring

### Vercel Analytics

Enable in project settings:
- Real User Monitoring (RUM)
- Web Vitals tracking
- Error tracking

### Custom Logging

Add to `lib/api.js`:
```javascript
export const logApiCall = (endpoint, duration, status) => {
  console.log(`[API] ${endpoint} - ${duration}ms - ${status}`)
  // Send to analytics service (e.g., Vercel Analytics)
}
```

## Changelog

### v0.1.0 (2026-02-03)
- Initial release
- OpenAI-style chat UI
- Video selector and history
- Scene search with CLIP
- On-demand clip extraction
- Vercel deployment ready

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check backend logs: `gcloud run logs read cloud-clip-api`
2. Check browser console for frontend errors
3. Review [CLOUD_CLIP_README.md](../CLOUD_CLIP_README.md) for backend troubleshooting

---

Built with Next.js 14, React 18, TailwindCSS, and deployed on Vercel.
