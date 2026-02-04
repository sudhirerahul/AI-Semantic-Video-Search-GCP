#!/bin/bash
set -e

echo "🏗️  Building FAISS index from ingested videos..."

export PROJECT_ID="gen-lang-client-0067393875"
export BUCKET_NAME="gen-lang-client-0067393875-media-1770102442"
export OUTPUT_DIR="./faiss_index"

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
echo "🚀 Running FAISS index builder..."
echo ""

python faiss_index_builder.py

echo ""
echo "✅ Index build complete!"
echo ""
echo "Index files created in: $OUTPUT_DIR"
ls -lh $OUTPUT_DIR

echo ""
echo "Next steps:"
echo "  1. Review index files in $OUTPUT_DIR"
echo "  2. Test search locally: ./test_search.sh"
echo "  3. Deploy to Cloud Run: ./deploy.sh"
