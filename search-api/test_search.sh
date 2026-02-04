#!/bin/bash
set -e

echo "🧪 Testing Video Search API locally..."
echo ""

# Check if index exists
if [ ! -f "./faiss_index/video_chunks.faiss" ]; then
    echo "❌ FAISS index not found. Run ./build_index.sh first."
    exit 1
fi

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
echo "🚀 Running search service test..."
echo ""

export PROJECT_ID="gen-lang-client-0067393875"
export BUCKET_NAME="gen-lang-client-0067393875-media-1770102442"

python search_service.py

echo ""
echo "✅ Test complete!"
echo ""
echo "To start API server:"
echo "  python api.py"
echo ""
echo "To test API with curl:"
echo '  curl -X POST http://localhost:8080/search -H "Content-Type: application/json" -d '"'"'{"query": "person walking", "top_k": 5}'"'"
