# Getting Started - Manual Setup

The automated startup script has issues with the CLIP model loading in background mode. Follow these manual steps instead:

## Step 1: Start Backend API (Terminal 1)

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/video-search-sa-key.json"

# Start API (stays in foreground)
worker/venv/bin/python search-api/cloud_clip_api.py
```

**Wait for:** "Loading CLIP embedding model..." then "Model loaded successfully"

**You'll see:** The Flask development server start message

**Leave this terminal running**

## Step 2: Start Frontend (Terminal 2)

Open a new terminal window:

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto/frontend

# Install dependencies (first time only)
npm install

# Create environment file (first time only)
echo "NEXT_PUBLIC_API_BASE=http://localhost:8080" > .env.local

# Start Next.js dev server
npm run dev
```

**Opens at:** http://localhost:3000

## Step 3: Test

1. Open http://localhost:3000 in your browser
2. Select a video from the left panel
3. Enter a search query (e.g., "person speaking")
4. Click Play on a scene card
5. Watch the clip in the right panel

## Troubleshooting

### Backend won't start

**Issue:** CLIP model hangs during loading

**Solution:**
```bash
# Try using system Python instead
python3 search-api/cloud_clip_api.py
```

### "Failed to fetch videos"

**Issue:** Backend not running or wrong URL

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8080/health

# Check .env.local
cat .env.local
```

### Port already in use

**Issue:** Another process using port 3000 or 8080

**Solution:**
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

## Quick Commands

### Stop Backend
Press `Ctrl+C` in Terminal 1

### Stop Frontend
Press `Ctrl+C` in Terminal 2

### Restart Frontend Only
Terminal 2:
```bash
npm run dev
```

### View Logs
Backend logs appear in Terminal 1
Frontend logs appear in Terminal 2

---

**Once both are running, open:** http://localhost:3000
