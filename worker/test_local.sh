#!/bin/bash
set -e

echo "🧪 Testing ingestion worker locally..."
echo ""
echo "This will:"
echo "  1. Install Python dependencies"
echo "  2. Run the worker on the sample video"
echo "  3. Generate index and assets"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "🚀 Running ingestion worker..."
echo ""

export PROJECT_ID="gen-lang-client-0067393875"
export BUCKET_NAME="gen-lang-client-0067393875-media-1770102442"

python ingest_worker.py gs://gen-lang-client-0067393875-media-1770102442/raw/sample_video.mp4

echo ""
echo "✅ Local test complete!"
echo ""
echo "Check GCS bucket for generated assets:"
echo "  gsutil ls gs://gen-lang-client-0067393875-media-1770102442/index/"
echo "  gsutil ls gs://gen-lang-client-0067393875-media-1770102442/thumbnails/"
echo "  gsutil ls gs://gen-lang-client-0067393875-media-1770102442/clips/"
