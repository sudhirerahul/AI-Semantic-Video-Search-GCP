# Quick Start Guide

Get the GCP Media frontend running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Backend API running (see main README)
- Git installed (for deployment)

---

## Local Development (3 steps)

### Option 1: Automated Start (Recommended)

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/frontend
./start_dev.sh
```

This script:
1. Starts backend API (port 8080)
2. Installs frontend dependencies
3. Creates `.env.local` with correct API URL
4. Starts Next.js dev server (port 3000)

**Opens at: http://localhost:3000**

### Option 2: Manual Start

```bash
# 1. Start backend API
cd /Users/sudhirerahul/Desktop/GCP_Media_proto
./start_cloud_clip.sh

# 2. Install frontend dependencies
cd frontend
npm install

# 3. Create environment file
echo "NEXT_PUBLIC_API_BASE=http://localhost:8080" > .env.local

# 4. Start dev server
npm run dev
```

**Opens at: http://localhost:3000**

---

## Production Deployment (10 minutes)

### Step 1: Push to GitHub (2 min)

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Initialize git (if not already done)
git init
git add .
git commit -m "feat: Add Next.js frontend"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/gcp-media-proto.git
git push -u origin main
```

### Step 2: Deploy Backend to Cloud Run (3 min)

```bash
cd search-api

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cloud-clip-api
gcloud run deploy cloud-clip-api \
  --image gcr.io/YOUR_PROJECT_ID/cloud-clip-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 300s \
  --allow-unauthenticated \
  --service-account YOUR_SERVICE_ACCOUNT \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,BUCKET_NAME=YOUR_BUCKET

# Note the service URL
gcloud run services describe cloud-clip-api \
  --region us-central1 \
  --format 'value(status.url)'
```

**Save this URL!** Example: `https://cloud-clip-api-abc123-uc.a.run.app`

### Step 3: Deploy Frontend to Vercel (5 min)

1. **Go to [vercel.com](https://vercel.com) and sign in**

2. **Click "Add New Project"**

3. **Import your GitHub repository**
   - Select `gcp-media-proto`
   - Set root directory: `frontend`

4. **Add environment variable:**
   - Name: `NEXT_PUBLIC_API_BASE`
   - Value: `https://cloud-clip-api-abc123-uc.a.run.app` (your Cloud Run URL)

5. **Click "Deploy"**

**Done!** Your app is live at `https://gcp-media-proto.vercel.app`

---

## Verify Deployment

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/frontend
./scripts/smoke_test.sh https://gcp-media-proto.vercel.app
```

Expected output:
```
✅ All critical tests passed!
```

---

## Troubleshooting

### "Failed to fetch videos"

**Fix:**
```bash
# Check backend is running
curl http://localhost:8080/health

# Check .env.local exists
cat .env.local
```

### "npm install" fails

**Fix:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### "Module not found" errors

**Fix:**
```bash
# Ensure you're in the frontend directory
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/frontend

# Reinstall dependencies
npm install
```

### Port 3000 already in use

**Fix:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

---

## Next Steps

### 1. Test Basic Flow

1. **Open http://localhost:3000**
2. **Select a video** from left panel
3. **Enter query** (e.g., "person speaking")
4. **Click "Play clip"** on a scene card
5. **Watch video** in right panel

### 2. Check History

1. **Run several queries**
2. **Click "History" tab** in left panel
3. **Click a history item** to reload results

### 3. Try New Conversation

1. **Click "New conversation"**
2. **Verify chat clears**
3. **Select different video**
4. **Run new query**

---

## Common Commands

```bash
# Start development
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run smoke tests
./scripts/smoke_test.sh http://localhost:3000

# View logs
tail -f /tmp/cloud_clip_api.log  # Backend
# Frontend logs shown in terminal

# Stop all services
killall -9 python node
```

---

## File Structure

```
frontend/
├── app/
│   ├── layout.js          # Root layout with Inter font
│   ├── globals.css        # Dark theme styles
│   └── page.js            # Main application
│
├── components/
│   ├── Header.jsx         # Top navigation
│   ├── LeftHistoryPanel.jsx   # Video selector + history
│   ├── ChatArea.jsx       # Chat interface
│   ├── SceneCard.jsx      # Scene thumbnail cards
│   └── VideoPlayerPanel.jsx   # Video player
│
├── lib/
│   └── api.js             # API wrapper functions
│
├── scripts/
│   └── smoke_test.sh      # Automated tests
│
├── package.json           # Dependencies
├── next.config.js         # Next.js config
├── tailwind.config.js     # Theme config
├── vercel.json            # Deployment config
└── .env.local             # Environment variables (local only)
```

---

## Environment Variables

### Local (`.env.local`)
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

### Production (Vercel Dashboard)
```bash
NEXT_PUBLIC_API_BASE=https://cloud-clip-api-abc123-uc.a.run.app
```

**Note:** Never commit `.env.local` to git!

---

## Resources

- **Full README**: [README.md](./README.md)
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Backend Docs**: [../CLOUD_CLIP_README.md](../CLOUD_CLIP_README.md)
- **Implementation Summary**: [../FRONTEND_IMPLEMENTATION_SUMMARY.md](../FRONTEND_IMPLEMENTATION_SUMMARY.md)

---

## Support

### Check Logs

```bash
# Backend API logs
tail -f /tmp/cloud_clip_api.log

# Frontend dev logs
# (shown in terminal where you ran npm run dev)

# Production logs (Vercel)
# Go to vercel.com > Project > Deployments > [deployment] > Logs
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Videos not loading | Check backend API is running |
| CORS errors | Update backend CORS config |
| Clip extraction fails | Check FFmpeg installed |
| Build errors | Clear node_modules, reinstall |
| Port conflicts | Kill processes or use different port |

---

## What's Next?

After getting it running:

1. **Read [README.md](./README.md)** for component details
2. **Follow [DEPLOYMENT.md](./DEPLOYMENT.md)** for production setup
3. **Customize the theme** in `tailwind.config.js`
4. **Add new features** following existing patterns

---

**Ready to build!** 🚀

Start with: `./start_dev.sh`
