# Complete Deployment Guide

Step-by-step instructions for deploying the GCP Media frontend to Vercel with Cloud Run backend.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] GCP project with billing enabled
- [ ] Videos uploaded to `gs://YOUR_BUCKET/videos/`
- [ ] Videos indexed (ran `video_indexer.py`)
- [ ] Service account with Storage Admin role
- [ ] GitHub account
- [ ] Vercel account (free tier works)
- [ ] `gcloud` CLI installed and authenticated
- [ ] Node.js 18+ installed locally

---

## Part 1: Deploy Backend to Cloud Run

### Step 1.1: Create Backend Dockerfile

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/search-api
```

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cloud_clip_api.py .

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "cloud_clip_api.py"]
```

### Step 1.2: Update CORS Configuration

Edit `cloud_clip_api.py` to allow Vercel domains:

```python
# Find the CORS initialization
CORS(app, origins=[
    'http://localhost:3000',
    'http://localhost:8000',
    'https://*.vercel.app',  # Allow all Vercel preview deployments
    # Add your production domain later
])
```

### Step 1.3: Build and Push Docker Image

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Build image
gcloud builds submit --tag gcr.io/$PROJECT_ID/cloud-clip-api

# Verify image exists
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

### Step 1.4: Deploy to Cloud Run

```bash
# Set variables
export BUCKET_NAME="your-bucket-name"
export SERVICE_ACCOUNT="video-search-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Deploy service
gcloud run deploy cloud-clip-api \
  --image gcr.io/$PROJECT_ID/cloud-clip-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --max-instances 10 \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars PROJECT_ID=$PROJECT_ID,BUCKET_NAME=$BUCKET_NAME

# Get the service URL
gcloud run services describe cloud-clip-api \
  --region us-central1 \
  --format 'value(status.url)'
```

**Save this URL!** You'll need it for the frontend deployment.

Example: `https://cloud-clip-api-abc123-uc.a.run.app`

### Step 1.5: Test Backend Deployment

```bash
# Set API URL
export API_URL="https://cloud-clip-api-abc123-uc.a.run.app"

# Test health endpoint
curl $API_URL/health

# Test videos endpoint
curl $API_URL/videos | jq

# Test query endpoint
curl -X POST $API_URL/query \
  -H "Content-Type: application/json" \
  -d '{"video_id": "VIDEO_ID_HERE", "query": "person", "top_k": 1}' | jq
```

If all tests pass, backend is ready!

---

## Part 2: Deploy Frontend to Vercel

### Step 2.1: Push Code to GitHub

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Initialize git (if not already done)
git init

# Create .gitignore for root
cat > .gitignore <<'EOF'
*.pyc
__pycache__/
.DS_Store
*.log
.env
.env.local
video-search-sa-key.json
venv/
node_modules/
.next/
EOF

# Add all files
git add .

# Commit
git commit -m "feat: Add Next.js frontend with OpenAI-style UI"

# Create GitHub repo (via web or CLI)
# Then add remote
git remote add origin https://github.com/YOUR_USERNAME/gcp-media-proto.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 2.2: Connect Vercel to GitHub

1. **Go to [vercel.com](https://vercel.com)**
2. **Sign in with GitHub**
3. **Click "Add New Project"**
4. **Select your repository:**
   - Find `gcp-media-proto` in the list
   - Click "Import"

### Step 2.3: Configure Vercel Project

**Framework Preset:** Next.js (should auto-detect)

**Root Directory:** `frontend` (IMPORTANT!)

**Build Settings:**
- Build Command: `npm run build` (auto-filled)
- Output Directory: `.next` (auto-filled)
- Install Command: `npm install` (auto-filled)

**Environment Variables:**

Add this environment variable:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_BASE` | `https://cloud-clip-api-abc123-uc.a.run.app` |

(Replace with your actual Cloud Run URL from Part 1)

**Click "Deploy"**

Deployment takes ~2 minutes.

### Step 2.4: Verify Deployment

Once deployed, you'll get a URL like:
```
https://gcp-media-proto.vercel.app
```

**Test the deployment:**

1. **Open the URL in your browser**
2. **Check browser console for errors**
3. **Verify videos load in left panel**
4. **Try a search query**
5. **Click Play on a scene**
6. **Verify video plays in right panel**

### Step 2.5: Run Smoke Tests

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/frontend

# Test deployment
./scripts/smoke_test.sh https://gcp-media-proto.vercel.app https://cloud-clip-api-abc123-uc.a.run.app
```

Expected output:
```
✅ All critical tests passed!
```

---

## Part 3: Custom Domain (Optional)

### Step 3.1: Add Domain in Vercel

1. **Go to Project Settings > Domains**
2. **Add your domain** (e.g., `clips.yourdomain.com`)
3. **Follow DNS configuration instructions:**
   - Add CNAME record: `clips` → `cname.vercel-dns.com`
   - Or A record → Vercel IP

### Step 3.2: Update Backend CORS

Add custom domain to `cloud_clip_api.py`:

```python
CORS(app, origins=[
    'http://localhost:3000',
    'https://*.vercel.app',
    'https://clips.yourdomain.com',  # Your custom domain
])
```

Redeploy backend:
```bash
cd search-api
gcloud builds submit --tag gcr.io/$PROJECT_ID/cloud-clip-api
gcloud run deploy cloud-clip-api --image gcr.io/$PROJECT_ID/cloud-clip-api
```

---

## Part 4: Continuous Deployment

### Automatic Deployments

Vercel automatically deploys on git push:

- **Main branch** → Production deployment
- **Other branches** → Preview deployments

### Deploy New Changes

```bash
# Make changes to code
git add .
git commit -m "feat: Add new feature"
git push

# Vercel automatically builds and deploys
# Check deployment status at vercel.com
```

### Preview Deployments

Every pull request gets a unique preview URL:
```
https://gcp-media-proto-git-feature-branch.vercel.app
```

---

## Part 5: Monitoring & Maintenance

### Enable Vercel Analytics

1. **Go to Project Settings > Analytics**
2. **Enable Web Analytics**
3. **View metrics:**
   - Page views
   - Unique visitors
   - Web Vitals (LCP, FID, CLS)

### Monitor Backend Logs

```bash
# View recent logs
gcloud run logs read cloud-clip-api \
  --region us-central1 \
  --limit 50

# Tail logs in real-time
gcloud run logs tail cloud-clip-api \
  --region us-central1
```

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Cloud Clip API Errors" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=60s
```

### Cost Monitoring

**Set budget alerts:**

```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="GCP Media Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## Troubleshooting

### Issue: Frontend shows "Failed to fetch videos"

**Diagnose:**
```bash
# Check backend is running
curl https://your-api.run.app/health

# Check CORS headers
curl -I -X OPTIONS https://your-api.run.app/videos \
  -H "Origin: https://your-frontend.vercel.app" \
  -H "Access-Control-Request-Method: GET"
```

**Fix:**
- Verify `NEXT_PUBLIC_API_BASE` environment variable in Vercel
- Check backend CORS configuration includes Vercel domain
- Redeploy backend after CORS changes

### Issue: Clip extraction times out

**Diagnose:**
```bash
# Check Cloud Run timeout
gcloud run services describe cloud-clip-api \
  --region us-central1 \
  --format 'value(spec.template.spec.timeoutSeconds)'
```

**Fix:**
```bash
# Increase timeout to 5 minutes
gcloud run services update cloud-clip-api \
  --timeout 300s \
  --region us-central1
```

### Issue: High costs

**Diagnose:**
```bash
# Check request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --format json

# Check instance count
gcloud run services describe cloud-clip-api \
  --region us-central1 \
  --format 'value(status.traffic[0].percent)'
```

**Fix:**
- Reduce `max-instances` to limit scale
- Enable request throttling
- Optimize video indexing (fewer shots)
- Increase clip expiry (reduce re-extraction)

### Issue: Videos not appearing after indexing

**Diagnose:**
```bash
# Check index files exist
gsutil ls gs://YOUR_BUCKET/index/

# Check shots.json format
gsutil cat gs://YOUR_BUCKET/index/VIDEO_ID/shots.json | jq
```

**Fix:**
- Verify video indexing completed successfully
- Check service account has `storage.objects.get` permission
- Restart Cloud Run service to clear cache

---

## Rollback Procedure

### Rollback Frontend (Vercel)

1. **Go to Vercel dashboard > Deployments**
2. **Find previous working deployment**
3. **Click "..." menu > "Promote to Production"**

Or via CLI:
```bash
vercel rollback
```

### Rollback Backend (Cloud Run)

```bash
# List revisions
gcloud run revisions list --service cloud-clip-api

# Rollback to previous revision
gcloud run services update-traffic cloud-clip-api \
  --to-revisions REVISION_NAME=100
```

---

## Security Best Practices

### 1. Service Account Permissions

Principle of least privilege:
```bash
# Review current permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$SERVICE_ACCOUNT"

# Remove unnecessary roles
gcloud projects remove-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/editor"

# Add minimal required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/storage.objectAdmin"
```

### 2. Rotate Service Account Keys

```bash
# Create new key
gcloud iam service-accounts keys create new-key.json \
  --iam-account=$SERVICE_ACCOUNT

# Update Cloud Run with new key (if using key-based auth)
# Better: Use Workload Identity (no keys needed)

# Delete old key after verifying
gcloud iam service-accounts keys delete OLD_KEY_ID \
  --iam-account=$SERVICE_ACCOUNT
```

### 3. Enable Workload Identity

```bash
# Create Kubernetes service account
kubectl create serviceaccount cloud-clip-sa

# Bind to GCP service account
gcloud iam service-accounts add-iam-policy-binding \
  $SERVICE_ACCOUNT \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[default/cloud-clip-sa]"
```

### 4. Add Rate Limiting

Update `cloud_clip_api.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

@app.route('/extract_clip', methods=['POST'])
@limiter.limit("5 per minute")  # Limit clip extraction
def extract_clip_endpoint():
    # ...
```

---

## Performance Optimization

### 1. Enable CDN for Static Assets

In `next.config.js`:
```javascript
module.exports = {
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
      },
    ],
  },
  // Enable SWC minification
  swcMinify: true,
}
```

### 2. Add Request Caching

Update `lib/api.js`:
```javascript
import useSWR from 'swr'

export const useVideos = () => {
  return useSWR('/videos', getVideos, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    dedupingInterval: 60000, // 1 minute
  })
}
```

### 3. Optimize Video Indexing

Reduce shot count for faster queries:
```bash
# In video_indexer.py, increase scene threshold
python video_indexer.py --scene-threshold 0.5  # Default: 0.3
```

Higher threshold = fewer shots = faster queries

---

## Scaling Recommendations

### Low Traffic (< 1K queries/month)
- Cloud Run: min-instances=0, max-instances=3
- Vercel: Free tier
- **Cost: ~$5/month**

### Medium Traffic (1K-10K queries/month)
- Cloud Run: min-instances=1, max-instances=10
- Vercel: Pro tier ($20/month)
- Enable Cloud CDN
- **Cost: ~$50/month**

### High Traffic (> 10K queries/month)
- Cloud Run: min-instances=2, max-instances=50
- Add load balancer with Cloud Armor
- Use Vertex AI Matching Engine for vector search
- Consider video CDN (Media CDN)
- **Cost: ~$500/month**

---

## Complete Checklist

### Pre-Deployment
- [ ] Videos uploaded to GCS
- [ ] Videos indexed with CLIP embeddings
- [ ] Service account created with correct permissions
- [ ] Local testing completed (`npm run dev`)
- [ ] Backend API tested locally

### Backend Deployment
- [ ] Dockerfile created
- [ ] CORS configuration updated
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Service URL obtained
- [ ] Health check passed
- [ ] API endpoints tested

### Frontend Deployment
- [ ] Code pushed to GitHub
- [ ] Vercel project created
- [ ] Root directory set to `frontend`
- [ ] Environment variable added
- [ ] Deployment successful
- [ ] Smoke tests passed
- [ ] Manual testing completed

### Post-Deployment
- [ ] Analytics enabled
- [ ] Monitoring configured
- [ ] Budget alerts set
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## Support Resources

- **Vercel Documentation**: https://vercel.com/docs
- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Next.js Documentation**: https://nextjs.org/docs
- **Backend README**: [CLOUD_CLIP_README.md](../CLOUD_CLIP_README.md)
- **Frontend README**: [README.md](./README.md)

---

**Deployment complete!** 🎉

Your GCP Media frontend is now live and ready to use.
