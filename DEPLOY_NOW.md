# 🚀 Deploy to Vercel - Quick Start

Your app is ready to deploy! Follow these 3 simple steps:

---

## Step 1: Deploy Backend (3 commands)

```bash
cd /Users/sudhirerahul/Desktop/GCP_Media_proto

# Run the deployment script
./deploy_to_cloud_run.sh

# Copy the API URL it prints (you'll need it for Step 3)
```

**Expected output:**
```
Service URL: https://cloud-clip-api-xxxxx-uc.a.run.app
```

**⚠️ SAVE THIS URL!**

---

## Step 2: Push to GitHub

```bash
# Still in /Users/sudhirerahul/Desktop/GCP_Media_proto

git init
git add .
git commit -m "Add AI video search with Gemini"

# Create repo at github.com/new first, then:
git remote add origin https://github.com/YOUR_USERNAME/gcp-media-proto.git
git push -u origin main
```

---

## Step 3: Deploy to Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub

2. **Click "Add New Project"**

3. **Import your repository** (`gcp-media-proto`)

4. **Configure:**
   - Root Directory: `frontend` ⚠️
   - Add Environment Variable:
     - Name: `NEXT_PUBLIC_API_BASE`
     - Value: `https://cloud-clip-api-xxxxx-uc.a.run.app` (from Step 1)

5. **Click "Deploy"**

---

## Done! 🎉

Your app will be live at:
```
https://gcp-media-frontend.vercel.app
```

**Share this URL with anyone!**

They can:
- Search videos with natural language
- AI-enhanced queries (Gemini 2.0)
- Watch clips instantly
- Dark, professional UI

---

## What's Included

✅ **Gemini 2.0 Flash** - Auto-enhances search queries
✅ **CLIP Vision** - Semantic video understanding
✅ **Cloud Run** - Auto-scaling backend
✅ **Next.js 14** - Fast, modern frontend
✅ **Vercel** - Global CDN hosting

---

## Cost

- **Free tier:** $0/month (< 100 requests/day)
- **Light usage:** ~$3/month (1K requests/month)

---

## Need Help?

See [VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md) for:
- Detailed instructions
- Troubleshooting
- Custom domains
- Monitoring
- Cost optimization

---

**Ready? Start with Step 1!** ⬆️
