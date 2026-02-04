#!/usr/bin/env python3
"""
Pub/Sub listener for Cloud Run.
Receives video upload events and triggers ingestion.
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from ingest_worker import VideoIngestionWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize worker (model loaded once at startup)
PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')

logger.info("Initializing Video Ingestion Worker...")
worker = VideoIngestionWorker(
    project_id=PROJECT_ID,
    bucket_name=BUCKET_NAME
)
logger.info("Worker initialized successfully!")


@app.route('/', methods=['POST'])
def pubsub_handler():
    """
    Handle Pub/Sub push messages.
    Message format from Pub/Sub:
    {
        "message": {
            "data": "<base64-encoded-json>",
            "messageId": "...",
            "publishTime": "..."
        }
    }
    """
    try:
        envelope = request.get_json()
        if not envelope:
            logger.error("No Pub/Sub message received")
            return ('Bad Request: no Pub/Sub message', 400)

        if 'message' not in envelope:
            logger.error("Invalid Pub/Sub message format")
            return ('Bad Request: invalid Pub/Sub message format', 400)

        pubsub_message = envelope['message']

        # Decode the message data
        import base64
        if 'data' in pubsub_message:
            message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
            event_data = json.loads(message_data)
        else:
            logger.error("No data in Pub/Sub message")
            return ('Bad Request: no data in message', 400)

        logger.info(f"Received event: {json.dumps(event_data, indent=2)}")

        # Extract video URI
        video_uri = event_data.get('video_uri')
        if not video_uri:
            logger.error("No video_uri in message")
            return ('Bad Request: no video_uri in message', 400)

        logger.info(f"Processing video: {video_uri}")

        # Process the video
        result = worker.process_video(video_uri)

        logger.info(f"Processing completed: {json.dumps(result, indent=2)}")

        return jsonify({
            'status': 'success',
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'project_id': PROJECT_ID,
        'bucket_name': BUCKET_NAME
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)
