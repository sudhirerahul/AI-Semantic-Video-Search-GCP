# Complete Vercel Deployment Guide
## Get Your App Live in 15 Minutes!

This guide will deploy:
- **Backend API** to Cloud Run (with Gemini AI)
- **Frontend** to Vercel
- **Shareable URL** you can send to anyone

---

## Part 1: Deploy Backend to Cloud Run (5 minutes)

The backend Docker build is already running. Once it completes:

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Deploy to Cloud Run
./deploy_to_cloud_run.sh
```

This will:
1. Build the Docker image with FFmpeg + CLIP + Gemini
2. Deploy to Cloud Run with autoscaling
3. Give you the API URL

**Save the API URL!** It will look like:
```
https://cloud-clip-api-xxxxx-uc.a.run.app
```

---

## Part 2: Push Code to GitHub (2 minutes)

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "feat: Add Next.js frontend with Gemini-powered search"

# Create repo on GitHub (do this first at github.com/new)
# Then add remote:
git remote add origin https://github.com/YOUR_USERNAME/gcp-media-proto.git

# Push
git push -u origin main
```

---

## Part 3: Deploy Frontend to Vercel (5 minutes)

### Step 3.1: Go to Vercel

1. Visit [vercel.com](https://vercel.com)
2. Sign in with GitHub
3. Click **"Add New Project"**

### Step 3.2: Import Repository

1. Select your GitHub repository: `gcp-media-proto`
2. Click **"Import"**

### Step 3.3: Configure Project

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** `frontend` ⚠️ **IMPORTANT!**

**Build Settings:** (auto-filled, don't change)
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

**Environment Variables:** Click "Add"

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_BASE` | `https://cloud-clip-api-xxxxx-uc.a.run.app` |

(Use your actual Cloud Run URL from Part 1)

### Step 3.4: Deploy

Click **"Deploy"**

Wait ~2 minutes for build to complete.

You'll get a URL like:
```
https://gcp-media-frontend.vercel.app
```

---

## Part 4: Test Your Deployment

### Test Backend

```bash
# Replace with your Cloud Run URL
API_URL="https://cloud-clip-api-xxxxx-uc.a.run.app"

# Test health
curl $API_URL/health

# Test videos
curl $API_URL/videos | jq
```

### Test Frontend

1. Open your Vercel URL in a browser
2. Select a video from the left panel
3. Enter a search query (e.g., "person speaking")
4. Click **Play** on a scene card
5. Watch the clip in the right panel

---

## Share Your App! 🎉

Send this link to anyone:
```
https://gcp-media-frontend.vercel.app
```

They can:
- Browse your indexed videos
- Search for scenes using natural language
- Watch clips instantly
- **Gemini AI enhances their queries automatically!**

---

## Features Enabled

✅ **Gemini 2.0 Flash** - Enhances search queries with visual details
✅ **CLIP ViT-B-32** - Semantic video search
✅ **On-demand clip extraction** - FFmpeg processing in the cloud
✅ **Auto-scaling** - Handles 0 to 1000s of requests
✅ **Signed URLs** - Secure GCS access with 60min expiry
✅ **Dark UI** - OpenAI-style interface with Inter font

---

## Cost Estimates

### Free Tier Usage (< 100 requests/day)
- Cloud Run: $0 (free tier)
- Vercel: $0 (hobby tier)
- **Total: FREE!**

### Light Usage (1000 requests/month)
- Cloud Run: ~$2
- Vercel: $0 (hobby tier)
- GCS: ~$0.50
- **Total: ~$2.50/month**

### Medium Usage (10K requests/month)
- Cloud Run: ~$20
- Vercel: $20 (Pro tier recommended)
- GCS: ~$5
- **Total: ~$45/month**

---

## Gemini Integration Details

### How It Works

When users search for "car", Gemini enhances it to:
> "A car driving on a road, automobile in motion, vehicle with wheels moving, car exterior visible in scene"

This expanded query helps CLIP find more relevant scenes!

### Disable Gemini (Optional)

To disable query enhancement, update the frontend API call:

```javascript
// In frontend/lib/api.js
export const queryScenes = async (video_id, query, top_k = 3) => {
  return fetchWithTimeout(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id,
      query,
      top_k,
      enhance_with_gemini: false  // Add this line
    })
  });
};
```

### Monitor Gemini Usage

```bash
# Check Cloud Run logs for Gemini enhancements
gcloud run logs read cloud-clip-api \
  --region us-central1 \
  --limit 50 | grep "Query enhanced"
```

---

## Updating Your Deployment

### Update Backend

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto
./deploy_to_cloud_run.sh
```

### Update Frontend

```bash
git add .
git commit -m "Update frontend"
git push
```

Vercel auto-deploys on every git push!

---

## Custom Domain (Optional)

### Add Custom Domain to Vercel

1. Go to Vercel Project Settings > Domains
2. Add your domain (e.g., `clips.yourdomain.com`)
3. Follow DNS configuration instructions

### Update Backend CORS

```python
# In search-api/cloud_clip_api.py
CORS(app, origins=[
    'http://localhost:3000',
    'https://*.vercel.app',
    'https://clips.yourdomain.com',  # Add your domain
])
```

Redeploy backend:
```bash
./deploy_to_cloud_run.sh
```

---

## Troubleshooting

### "Failed to fetch videos"

**Cause:** Frontend can't reach backend

**Fix:**
1. Verify `NEXT_PUBLIC_API_BASE` in Vercel settings
2. Check backend CORS includes `*.vercel.app`
3. Test backend: `curl https://your-api.run.app/health`

### "Clip extraction times out"

**Cause:** Cloud Run timeout too short

**Fix:**
```bash
gcloud run services update cloud-clip-api \
  --timeout 300s \
  --region us-central1
```

### Gemini not working

**Check logs:**
```bash
gcloud run logs read cloud-clip-api \
  --region us-central1 \
  --limit 100 | grep -i gemini
```

**Common issues:**
- Vertex AI API not enabled: Run `gcloud services enable aiplatform.googleapis.com`
- Service account needs `aiplatform.user` role

---

## Monitoring

### View Backend Logs

```bash
# Real-time logs
gcloud run logs tail cloud-clip-api --region us-central1

# Recent logs
gcloud run logs read cloud-clip-api --region us-central1 --limit 50
```

### View Frontend Logs

1. Go to vercel.com
2. Select your project
3. Click **Deployments** > [latest deployment] > **Logs**

### Monitor Costs

```bash
# View Cloud Run metrics
gcloud run services describe cloud-clip-api \
  --region us-central1 \
  --format 'value(status.traffic)'

# Set budget alert
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="GCP Media Budget" \
  --budget-amount=50USD
```

---

## Support

### Backend Issues

Check Cloud Run logs:
```bash
gcloud run logs read cloud-clip-api --region us-central1 --limit 100
```

### Frontend Issues

Check browser console (F12 > Console tab)

### Get Help

1. Check [frontend/README.md](frontend/README.md) for detailed docs
2. Check [frontend/DEPLOYMENT.md](frontend/DEPLOYMENT.md) for advanced deployment
3. Review Cloud Run logs for backend errors

---

## Success Checklist

Before sharing your app, verify:

- [ ] Backend health check returns `{"status": "healthy"}`
- [ ] Videos load in frontend left panel
- [ ] Search returns results
- [ ] Clip playback works
- [ ] Gemini enhancement appears in logs
- [ ] No console errors in browser
- [ ] Tested in incognito mode

---

## Next Steps

### Add More Videos

1. Upload videos to `gs://YOUR_BUCKET/videos/`
2. Run video indexer:
   ```bash
   cd worker
   source venv/bin/activate
   python video_indexer.py
   ```
3. Refresh frontend - new videos appear!

### Customize UI

Edit `frontend/tailwind.config.js` to change colors, fonts, etc.

### Enable Analytics

In Vercel project settings:
1. Go to **Analytics**
2. Enable **Web Analytics**
3. View real-time usage stats

---

**You're all set!** 🚀

Your AI-powered video search app is now live and shareable.

**Your Live App:** `https://gcp-media-frontend.vercel.app`
