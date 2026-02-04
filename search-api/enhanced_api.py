#!/usr/bin/env python3
"""
Enhanced Flask API for Video Search Service with Upload & Processing

New Endpoints:
- POST /upload - Upload video file for processing
- GET /status/{video_id} - Check processing status
- POST /search - Search for video scenes (enhanced with video_id filter)
- GET /health - Health check
"""

import os
import json
import logging
import uuid
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from google.cloud import storage
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
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
WORKER_PATH = os.environ.get('WORKER_PATH', '../worker/ingest_worker.py')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# In-memory processing status (TODO: use Redis/DB for production)
processing_status = {}

# Initialize search service (loaded once at startup)
logger.info("Initializing Video Search Service...")
search_service = VideoSearchService(
    project_id=PROJECT_ID,
    bucket_name=BUCKET_NAME,
    index_path=INDEX_PATH,
    metadata_path=METADATA_PATH
)
logger.info("Search service initialized successfully!")


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_video_async(video_id, video_path, video_uri):
    """
    Process video asynchronously using the ingestion worker.
    This runs in a background thread.
    """
    try:
        logger.info(f"Starting async processing for video {video_id}")
        processing_status[video_id]['state'] = 'processing'
        processing_status[video_id]['progress'] = 10
        processing_status[video_id]['updated_at'] = datetime.utcnow().isoformat()

        # Run the ingestion worker
        # Note: In production, this should be a proper job queue (Cloud Tasks, Celery, etc.)
        # Use the worker's virtual environment Python
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_python = os.path.join(project_root, 'worker', 'venv', 'bin', 'python')

        worker_cmd = [
            venv_python,
            WORKER_PATH,
            '--video-uri', video_uri,
            '--project-id', PROJECT_ID,
            '--bucket-name', BUCKET_NAME
        ]

        logger.info(f"Running worker: {' '.join(worker_cmd)}")

        # Simulate progress updates (in production, worker would report progress)
        processing_status[video_id]['progress'] = 30

        result = subprocess.run(
            worker_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            # Parse worker output
            try:
                # Extract JSON from last line
                output_lines = result.stdout.strip().split('\n')
                worker_result = None
                for line in reversed(output_lines):
                    try:
                        worker_result = json.loads(line)
                        break
                    except:
                        continue

                if worker_result:
                    processing_status[video_id]['state'] = 'completed'
                    processing_status[video_id]['progress'] = 100
                    processing_status[video_id]['total_chunks'] = worker_result.get('total_chunks', 0)
                    processing_status[video_id]['updated_at'] = datetime.utcnow().isoformat()
                    logger.info(f"Video {video_id} processed successfully: {worker_result.get('total_chunks', 0)} chunks")
                else:
                    raise Exception("Could not parse worker output")
            except Exception as e:
                logger.error(f"Error parsing worker output: {e}")
                processing_status[video_id]['state'] = 'completed'
                processing_status[video_id]['progress'] = 100
        else:
            error_msg = result.stderr or "Worker failed"
            logger.error(f"Worker failed for video {video_id}: {error_msg}")
            processing_status[video_id]['state'] = 'failed'
            processing_status[video_id]['error'] = error_msg
            processing_status[video_id]['updated_at'] = datetime.utcnow().isoformat()

    except subprocess.TimeoutExpired:
        logger.error(f"Processing timeout for video {video_id}")
        processing_status[video_id]['state'] = 'failed'
        processing_status[video_id]['error'] = 'Processing timeout (10 minutes)'
        processing_status[video_id]['updated_at'] = datetime.utcnow().isoformat()
    except Exception as e:
        logger.error(f"Processing error for video {video_id}: {e}", exc_info=True)
        processing_status[video_id]['state'] = 'failed'
        processing_status[video_id]['error'] = str(e)
        processing_status[video_id]['updated_at'] = datetime.utcnow().isoformat()
    finally:
        # Clean up local file
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up local file: {video_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file: {e}")


@app.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file for processing.

    Request: multipart/form-data with 'video' file field

    Response:
    {
        "video_id": "abc123",
        "filename": "my_video.mp4",
        "size": 12345678,
        "state": "queued",
        "message": "Video uploaded successfully. Processing started."
    }
    """
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        file = request.files['video']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Generate unique video ID
        video_id = str(uuid.uuid4())[:8]
        original_filename = secure_filename(file.filename)
        filename = f"{video_id}_{original_filename}"

        # Save file locally (temporary)
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(local_path)
        file_size = os.path.getsize(local_path)

        logger.info(f"Video uploaded: {filename} ({file_size} bytes)")

        # Upload to GCS
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"raw/{filename}"
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(local_path)
        video_uri = f"gs://{BUCKET_NAME}/{blob_name}"

        logger.info(f"Video uploaded to GCS: {video_uri}")

        # Initialize processing status
        processing_status[video_id] = {
            'video_id': video_id,
            'filename': original_filename,
            'video_uri': video_uri,
            'state': 'queued',
            'progress': 0,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Start async processing
        thread = threading.Thread(
            target=process_video_async,
            args=(video_id, local_path, video_uri)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'video_id': video_id,
            'filename': original_filename,
            'size': file_size,
            'state': 'queued',
            'message': 'Video uploaded successfully. Processing started.'
        }), 200

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/status/<video_id>', methods=['GET'])
def get_status(video_id):
    """
    Get processing status for a video.

    Response:
    {
        "video_id": "abc123",
        "state": "processing",  // queued | processing | completed | failed
        "progress": 65,
        "total_chunks": 128,
        "error": null,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:01:00"
    }
    """
    if video_id not in processing_status:
        return jsonify({'error': 'Video not found'}), 404

    return jsonify(processing_status[video_id]), 200


@app.route('/search', methods=['POST'])
def search():
    """
    Search for video scenes.

    Request body:
    {
        "query": "person walking outdoors",
        "video_id": "abc123",  // optional: filter by specific video
        "top_k": 10,
        "enable_temporal_merge": true,
        "min_score": 0.0
    }
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'Missing required field: query'}), 400

        query = data['query']
        video_id_filter = data.get('video_id')
        top_k = data.get('top_k', 10)
        enable_temporal_merge = data.get('enable_temporal_merge', True)
        min_score = data.get('min_score', 0.0)

        logger.info(f"Search request: query='{query}', video_id={video_id_filter}, top_k={top_k}")

        # Perform search
        result = search_service.search(
            query=query,
            top_k=top_k,
            enable_temporal_merge=enable_temporal_merge,
            enable_signed_urls=True,
            min_score=min_score
        )

        # Filter by video_id if specified
        if video_id_filter:
            result['results'] = [
                r for r in result['results']
                if video_id_filter in r.get('video_id', '')
            ]
            result['total_results'] = len(result['results'])

        # Clean up results
        for r in result['results']:
            r.pop('chunks', None)
            r.pop('index_id', None)
            r.pop('text_boost', None)
            r.pop('duration_penalty', None)
            r.pop('thumbnail_uri', None)
            r.pop('clip_uri', None)
            r.pop('video_uri', None)

        logger.info(f"Search completed: {result['total_results']} results in {result['timing']['total_ms']:.0f}ms")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'video-search-api-enhanced',
        'total_chunks': search_service.total_chunks,
        'embedding_dim': search_service.embedding_dim,
        'project_id': PROJECT_ID,
        'bucket_name': BUCKET_NAME,
        'features': ['upload', 'async_processing', 'search', 'status_tracking']
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info."""
    return jsonify({
        'service': 'Video Search API (Enhanced)',
        'version': '2.0.0',
        'level': 3,
        'features': [
            'Video upload',
            'Async processing',
            'Multi-modal embeddings (CLIP)',
            'Two-stage retrieval (recall + rerank)',
            'Temporal merging',
            'Signed URLs',
            'Sub-second search latency'
        ],
        'endpoints': {
            'POST /upload': 'Upload video for processing',
            'GET /status/{video_id}': 'Check processing status',
            'POST /search': 'Search for video scenes',
            'GET /health': 'Health check'
        },
        'stats': {
            'total_chunks': search_service.total_chunks,
            'embedding_dim': search_service.embedding_dim,
            'videos_processing': len([v for v in processing_status.values() if v['state'] in ['queued', 'processing']])
        }
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting enhanced server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
