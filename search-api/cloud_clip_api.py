#!/usr/bin/env python3
"""
Cloud Clip Extraction API - On-demand clip generation from GCS videos
Endpoints: /videos, /query, /extract_clip
"""

import os
import json
import logging
import tempfile
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import storage
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[
    'http://localhost:3000',
    'http://localhost:8000',
    'https://*.vercel.app',
    'https://vercel.app'
])

# Configuration
PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Initialize clients
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# Configure Gemini (use Vertex AI with service account)
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        # Use Vertex AI with default credentials (service account)
        genai.configure(
            credentials=storage_client._credentials,
            project=PROJECT_ID,
            location='us-central1'
        )
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("Gemini AI configured successfully with Vertex AI")
except Exception as e:
    gemini_model = None
    logger.warning(f"Gemini configuration failed: {e} - query enhancement disabled")

# Lazy load embedding model (only when first needed)
embedding_model = None

def get_embedding_model():
    """Lazy load the CLIP model on first use"""
    global embedding_model
    if embedding_model is None:
        logger.info("Loading CLIP embedding model...")
        embedding_model = SentenceTransformer('clip-ViT-B-32')
        logger.info("Model loaded successfully")
    return embedding_model


def enhance_query_with_gemini(query: str) -> str:
    """Use Gemini to enhance and expand the search query"""
    if not gemini_model:
        return query

    try:
        prompt = f"""Given this video search query, expand it with visual details that would help find matching scenes.
Focus on visual elements, actions, objects, and settings.
Keep it concise (under 50 words).

Query: {query}

Enhanced query:"""

        response = gemini_model.generate_content(prompt)
        enhanced = response.text.strip()
        logger.info(f"Query enhanced: '{query}' -> '{enhanced}'")
        return enhanced
    except Exception as e:
        logger.error(f"Gemini query enhancement failed: {e}")
        return query


def generate_signed_url(blob_name: str, expiration_minutes: int = 60) -> str:
    """Generate public URL for GCS object (bucket is publicly readable)"""
    # Use public URL since bucket is set to public read
    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
    return public_url


def load_video_index(video_id: str) -> dict:
    """Load shots.json for a video"""
    blob = bucket.blob(f'index/{video_id}/shots.json')
    if not blob.exists():
        raise FileNotFoundError(f"Index not found for video {video_id}")

    data = json.loads(blob.download_as_text())
    return data


def load_video_embeddings(video_id: str) -> dict:
    """Load embeddings.json for a video"""
    blob = bucket.blob(f'index/{video_id}/embeddings.json')
    if not blob.exists():
        raise FileNotFoundError(f"Embeddings not found for video {video_id}")

    data = json.loads(blob.download_as_text())
    return data


def compute_query_embedding(query: str) -> np.ndarray:
    """Compute embedding for text query"""
    model = get_embedding_model()
    embedding = model.encode([query], convert_to_numpy=True)[0]
    return embedding


def search_shots(video_id: str, query: str, top_k: int = 3) -> list:
    """
    Search for shots matching the query
    Returns top K shots with scores
    """
    logger.info(f"Searching video {video_id} for: {query}")

    # Load embeddings
    embeddings_data = load_video_embeddings(video_id)
    index_data = load_video_index(video_id)

    # Compute query embedding
    query_emb = compute_query_embedding(query)

    # Compute similarities
    results = []
    for emb_doc in embeddings_data:
        shot_emb = np.array(emb_doc['embedding'])

        # Cosine similarity
        similarity = np.dot(query_emb, shot_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(shot_emb)
        )

        shot_idx = emb_doc['shot_index']
        shot_info = index_data['shots'][shot_idx]

        results.append({
            'shot_index': shot_idx,
            'start': shot_info['start'],
            'end': shot_info['end'],
            'thumbnail_gcs': shot_info['thumbnail_gcs'],
            'score': float(similarity)
        })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    # Return top K
    return results[:top_k]


def extract_clip_from_gcs(video_gcs_path: str, start: float, end: float, output_gcs_path: str):
    """
    Extract clip from GCS video using FFmpeg
    Downloads video, extracts clip, uploads to GCS
    """
    logger.info(f"Extracting clip: {start}s - {end}s from {video_gcs_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download video
        video_local = os.path.join(tmpdir, 'video.mp4')
        blob_name = video_gcs_path.replace(f'gs://{BUCKET_NAME}/', '')
        blob = bucket.blob(blob_name)

        logger.info(f"Downloading video from GCS...")
        blob.download_to_filename(video_local)

        # Extract clip with FFmpeg (fast seek)
        clip_local = os.path.join(tmpdir, 'clip.mp4')
        duration = end - start

        cmd = [
            'ffmpeg',
            '-ss', str(start),  # Seek before input (fast)
            '-i', video_local,
            '-t', str(duration),
            '-c', 'copy',  # Stream copy (fast, no re-encode)
            '-y',
            clip_local
        ]

        logger.info(f"Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, timeout=60)

        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr.decode()}")
            raise RuntimeError("Clip extraction failed")

        # Upload clip to GCS
        logger.info(f"Uploading clip to {output_gcs_path}")
        clip_blob = bucket.blob(output_gcs_path.replace(f'gs://{BUCKET_NAME}/', ''))
        clip_blob.upload_from_filename(clip_local, content_type='video/mp4')

        logger.info(f"Clip extracted successfully")


@app.route('/videos', methods=['GET'])
def list_videos():
    """
    List all pre-indexed videos with metadata

    Returns:
    [
        {
            "video_id": "videoplayback_abc123",
            "title": "Video 1",
            "num_shots": 15,
            "duration": 120.5,
            "poster_thumbnail_url": "https://..."
        }
    ]
    """
    try:
        # List all shots.json files to find indexed videos
        blobs = bucket.list_blobs(prefix='index/')
        video_ids = set()

        for blob in blobs:
            # Look for shots.json files: index/video_id/shots.json
            if blob.name.endswith('/shots.json'):
                parts = blob.name.split('/')
                if len(parts) >= 3:
                    video_id = parts[1]
                    video_ids.add(video_id)

        video_ids = list(video_ids)

        # Load metadata for each video
        videos = []
        for video_id in video_ids:
            try:
                index_data = load_video_index(video_id)

                # Get first thumbnail as poster
                if index_data['shots']:
                    first_shot = index_data['shots'][0]
                    thumbnail_blob_name = first_shot['thumbnail_gcs'].replace(f'gs://{BUCKET_NAME}/', '')
                    poster_url = generate_signed_url(thumbnail_blob_name)
                else:
                    poster_url = None

                # Calculate duration
                if index_data['shots']:
                    duration = index_data['shots'][-1]['end']
                else:
                    duration = 0

                videos.append({
                    'video_id': video_id,
                    'title': video_id.replace('_', ' ').title(),
                    'num_shots': index_data['num_shots'],
                    'duration': round(duration, 1),
                    'poster_thumbnail_url': poster_url,
                    'indexed_at': index_data.get('created_at')
                })
            except Exception as e:
                logger.error(f"Failed to load metadata for {video_id}: {e}")
                continue

        logger.info(f"Returning {len(videos)} videos")
        return jsonify(videos), 200

    except Exception as e:
        logger.error(f"Error listing videos: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query_video():
    """
    Search for shots in a video using natural language

    Request:
    {
        "video_id": "videoplayback_abc123",
        "query": "person speaking to camera",
        "top_k": 3
    }

    Response:
    [
        {
            "shot_index": 5,
            "start": 12.5,
            "end": 16.8,
            "thumbnail_url": "https://...",
            "score": 0.87
        }
    ]
    """
    try:
        data = request.get_json()

        if not data or 'video_id' not in data or 'query' not in data:
            return jsonify({'error': 'Missing required fields: video_id, query'}), 400

        video_id = data['video_id']
        query = data['query']
        top_k = data.get('top_k', 3)
        use_gemini = data.get('enhance_with_gemini', True)

        logger.info(f"Query: '{query}' for video {video_id}, top_k={top_k}")

        # Enhance query with Gemini if enabled
        search_query = enhance_query_with_gemini(query) if use_gemini else query

        # Search
        results = search_shots(video_id, search_query, top_k)

        # Add signed URLs for thumbnails
        for result in results:
            thumbnail_blob_name = result['thumbnail_gcs'].replace(f'gs://{BUCKET_NAME}/', '')
            result['thumbnail_url'] = generate_signed_url(thumbnail_blob_name)
            # Remove GCS path from response
            del result['thumbnail_gcs']

        logger.info(f"Found {len(results)} matching shots")

        return jsonify(results), 200

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/extract_clip', methods=['POST'])
def extract_clip():
    """
    Extract clip on-demand from cloud video

    Request:
    {
        "video_id": "videoplayback_abc123",
        "shot_index": 5
    }

    Response:
    {
        "clip_url": "https://...",
        "thumbnail_url": "https://...",
        "start": 12.5,
        "end": 16.8,
        "video_id": "videoplayback_abc123",
        "expires_at": "2024-01-01T13:00:00Z"
    }
    """
    try:
        data = request.get_json()

        if not data or 'video_id' not in data or 'shot_index' not in data:
            return jsonify({'error': 'Missing required fields: video_id, shot_index'}), 400

        video_id = data['video_id']
        shot_index = data['shot_index']

        logger.info(f"Extracting clip for video {video_id}, shot {shot_index}")

        # Load index
        index_data = load_video_index(video_id)

        if shot_index >= len(index_data['shots']):
            return jsonify({'error': f'Shot index {shot_index} out of range'}), 400

        shot = index_data['shots'][shot_index]
        video_gcs_path = index_data['video_gcs_path']

        # Define output path
        clip_gcs_path = f'gs://{BUCKET_NAME}/extracts/{video_id}/clips/{video_id}_shot{shot_index:04d}_clip.mp4'

        # Check if clip already exists
        clip_blob_name = clip_gcs_path.replace(f'gs://{BUCKET_NAME}/', '')
        clip_blob = bucket.blob(clip_blob_name)

        if not clip_blob.exists():
            # Extract clip
            extract_clip_from_gcs(
                video_gcs_path,
                shot['start'],
                shot['end'],
                clip_gcs_path
            )
        else:
            logger.info(f"Clip already exists, reusing")

        # Generate signed URLs
        clip_url = generate_signed_url(clip_blob_name, expiration_minutes=60)

        thumbnail_blob_name = shot['thumbnail_gcs'].replace(f'gs://{BUCKET_NAME}/', '')
        thumbnail_url = generate_signed_url(thumbnail_blob_name, expiration_minutes=60)

        expires_at = (datetime.utcnow() + timedelta(minutes=60)).isoformat() + 'Z'

        response = {
            'clip_url': clip_url,
            'thumbnail_url': thumbnail_url,
            'start': shot['start'],
            'end': shot['end'],
            'duration': round(shot['end'] - shot['start'], 1),
            'video_id': video_id,
            'shot_index': shot_index,
            'expires_at': expires_at
        }

        logger.info(f"Clip ready: {clip_url}")

        return jsonify(response), 200

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Clip extraction error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-clip-api',
        'project_id': PROJECT_ID,
        'bucket_name': BUCKET_NAME,
        'features': ['video_list', 'semantic_search', 'on_demand_clip_extraction']
    }), 200


@app.route('/', methods=['GET'])
def root():
    """API info"""
    return jsonify({
        'service': 'Cloud Clip Extraction API',
        'version': '1.0.0',
        'endpoints': {
            'GET /videos': 'List pre-indexed videos',
            'POST /query': 'Search for shots using natural language',
            'POST /extract_clip': 'Extract clip on-demand from cloud video',
            'GET /health': 'Health check'
        }
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Cloud Clip API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
