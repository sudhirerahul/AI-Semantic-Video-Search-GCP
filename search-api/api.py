#!/usr/bin/env python3
"""
Flask API for Video Search Service

Endpoints:
- POST /search - Search for video scenes
- GET /health - Health check
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from search_service import VideoSearchService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for web clients

# Configuration
PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')
INDEX_PATH = os.environ.get('INDEX_PATH', './faiss_index/video_chunks.faiss')
METADATA_PATH = os.environ.get('METADATA_PATH', './faiss_index/video_chunks_metadata.json')

# Initialize search service (loaded once at startup)
logger.info("Initializing Video Search Service...")
search_service = VideoSearchService(
    project_id=PROJECT_ID,
    bucket_name=BUCKET_NAME,
    index_path=INDEX_PATH,
    metadata_path=METADATA_PATH
)
logger.info("Search service initialized successfully!")


@app.route('/search', methods=['POST'])
def search():
    """
    Search for video scenes.

    Request body:
    {
        "query": "person walking outdoors",
        "top_k": 10,
        "enable_temporal_merge": true,
        "min_score": 0.0
    }

    Response:
    {
        "query": "person walking outdoors",
        "total_results": 5,
        "results": [
            {
                "video_id": "sample_video_abc123",
                "video_name": "sample_video",
                "start_time": 10.5,
                "end_time": 15.2,
                "duration": 4.7,
                "avg_score": 0.85,
                "thumbnail_url": "https://...",
                "clip_url": "https://...",
                "merged": true,
                "num_chunks": 2
            },
            ...
        ],
        "timing": {
            "total_ms": 245
        }
    }
    """
    try:
        # Parse request
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing required field: query'
            }), 400

        query = data['query']
        top_k = data.get('top_k', 10)
        enable_temporal_merge = data.get('enable_temporal_merge', True)
        min_score = data.get('min_score', 0.0)

        logger.info(f"Search request: query='{query}', top_k={top_k}")

        # Perform search
        result = search_service.search(
            query=query,
            top_k=top_k,
            enable_temporal_merge=enable_temporal_merge,
            enable_signed_urls=True,
            min_score=min_score
        )

        # Clean up results for response (remove internal fields)
        for r in result['results']:
            # Remove internal fields
            r.pop('chunks', None)
            r.pop('index_id', None)
            r.pop('text_boost', None)
            r.pop('duration_penalty', None)

            # Keep only essential fields
            r.pop('thumbnail_uri', None)
            r.pop('clip_uri', None)
            r.pop('video_uri', None)

        logger.info(f"Search completed: {result['total_results']} results in {result['timing']['total_ms']:.0f}ms")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'video-search-api',
        'total_chunks': search_service.total_chunks,
        'embedding_dim': search_service.embedding_dim,
        'project_id': PROJECT_ID,
        'bucket_name': BUCKET_NAME
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info."""
    return jsonify({
        'service': 'Video Search API',
        'version': '1.0.0',
        'level': 3,
        'features': [
            'Multi-modal embeddings (CLIP)',
            'Two-stage retrieval (recall + rerank)',
            'Temporal merging',
            'Signed URLs',
            'Sub-second search latency'
        ],
        'endpoints': {
            'POST /search': 'Search for video scenes',
            'GET /health': 'Health check'
        },
        'stats': {
            'total_chunks': search_service.total_chunks,
            'embedding_dim': search_service.embedding_dim
        }
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
