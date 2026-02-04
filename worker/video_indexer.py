#!/usr/bin/env python3
"""
Video Indexing System - Offline preprocessing for cloud-stored videos
Detects shot boundaries, generates thumbnails, computes embeddings
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import hashlib

from google.cloud import storage
import numpy as np
from sentence_transformers import SentenceTransformer
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoIndexer:
    """Index videos in GCS: detect shots, generate thumbnails, compute embeddings"""

    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)

        # Load embedding model (CLIP for multi-modal)
        logger.info("Loading CLIP embedding model...")
        self.model = SentenceTransformer('clip-ViT-B-32')
        logger.info("Model loaded successfully")

    def list_videos(self) -> List[str]:
        """List all videos in gs://bucket/videos/"""
        blobs = list(self.bucket.list_blobs(prefix='videos/'))
        videos = [blob.name for blob in blobs if blob.name.endswith(('.mp4', '.mov', '.avi'))]
        logger.info(f"Found {len(videos)} videos in GCS")
        return videos

    def get_video_id(self, video_path: str) -> str:
        """Generate stable video ID from path"""
        # Use basename without extension + hash of path
        basename = Path(video_path).stem
        # Clean up the name
        clean_name = basename.replace(' ', '_').replace('(', '').replace(')', '')
        # Add short hash for uniqueness
        path_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
        return f"{clean_name}_{path_hash}"

    def detect_shots(self, video_path: str, threshold: float = 0.3) -> List[Dict[str, float]]:
        """
        Detect shot boundaries using FFmpeg scene detection
        Returns list of shots with start/end times
        """
        logger.info(f"Detecting shots in {video_path} (threshold={threshold})")

        # Use FFmpeg to detect scene changes
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', f'select=\'gt(scene,{threshold})\',showinfo',
            '-f', 'null',
            '-'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse scene timestamps from FFmpeg output
            timestamps = [0.0]  # Always start with 0
            for line in result.stderr.split('\n'):
                if 'pts_time:' in line:
                    try:
                        # Extract timestamp
                        parts = line.split('pts_time:')
                        if len(parts) > 1:
                            time_str = parts[1].split()[0]
                            timestamp = float(time_str)
                            timestamps.append(timestamp)
                    except (ValueError, IndexError):
                        continue

            # Get video duration
            duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip())

            # Create shots from timestamps
            shots = []
            timestamps.append(duration)  # Add end
            timestamps = sorted(set(timestamps))  # Remove duplicates and sort

            for i in range(len(timestamps) - 1):
                shots.append({
                    'shot_index': i,
                    'start': round(timestamps[i], 3),
                    'end': round(timestamps[i + 1], 3)
                })

            logger.info(f"Detected {len(shots)} shots")
            return shots

        except subprocess.TimeoutExpired:
            logger.error("Shot detection timed out")
            raise
        except Exception as e:
            logger.error(f"Shot detection failed: {e}")
            raise

    def extract_thumbnail(self, video_path: str, timestamp: float, output_path: str):
        """Extract thumbnail at specific timestamp"""
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]

        subprocess.run(cmd, capture_output=True, check=True, timeout=30)

    def compute_embedding(self, image_path: str) -> List[float]:
        """Compute CLIP embedding for thumbnail image"""
        from PIL import Image

        img = Image.open(image_path)
        # CLIP model expects RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Encode image
        embedding = self.model.encode(img, convert_to_numpy=True)
        return embedding.tolist()

    def index_video(self, video_gcs_path: str) -> Dict[str, Any]:
        """
        Index a single video:
        1. Download from GCS
        2. Detect shots
        3. Extract thumbnails
        4. Compute embeddings
        5. Upload index to GCS
        """
        logger.info(f"Indexing video: {video_gcs_path}")

        video_id = self.get_video_id(video_gcs_path)
        logger.info(f"Video ID: {video_id}")

        # Check if already indexed
        index_blob = self.bucket.blob(f'index/{video_id}/shots.json')
        if index_blob.exists():
            logger.info(f"Video {video_id} already indexed, skipping")
            # Download and return existing index
            index_data = json.loads(index_blob.download_as_text())
            return index_data

        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Download video
            video_local_path = os.path.join(tmpdir, 'video.mp4')
            logger.info(f"Downloading video from {video_gcs_path}")

            blob = self.bucket.blob(video_gcs_path.replace(f'gs://{self.bucket_name}/', ''))
            blob.download_to_filename(video_local_path)

            # Detect shots
            shots = self.detect_shots(video_local_path)

            # Process each shot
            embeddings = []
            for shot in shots:
                shot_idx = shot['shot_index']
                timestamp = (shot['start'] + shot['end']) / 2  # Middle of shot

                # Extract thumbnail
                thumb_local = os.path.join(tmpdir, f'thumb_{shot_idx:04d}.jpg')
                self.extract_thumbnail(video_local_path, timestamp, thumb_local)

                # Upload thumbnail to GCS
                thumb_gcs_path = f'index/{video_id}/thumbs/thumb_{shot_idx:04d}.jpg'
                thumb_blob = self.bucket.blob(thumb_gcs_path)
                thumb_blob.upload_from_filename(thumb_local, content_type='image/jpeg')

                # Compute embedding
                embedding = self.compute_embedding(thumb_local)

                # Add to shot metadata
                shot['thumbnail_gcs'] = f'gs://{self.bucket_name}/{thumb_gcs_path}'
                shot['embedding_id'] = f'{video_id}_shot_{shot_idx:04d}'

                embeddings.append({
                    'embedding_id': shot['embedding_id'],
                    'shot_index': shot_idx,
                    'embedding': embedding
                })

                logger.info(f"Processed shot {shot_idx}/{len(shots)}")

            # Create index document
            index_doc = {
                'video_id': video_id,
                'video_gcs_path': video_gcs_path,
                'created_at': datetime.utcnow().isoformat(),
                'num_shots': len(shots),
                'shots': shots
            }

            # Save shots.json
            shots_blob = self.bucket.blob(f'index/{video_id}/shots.json')
            shots_blob.upload_from_string(
                json.dumps(index_doc, indent=2),
                content_type='application/json'
            )

            # Save embeddings.json
            embeddings_blob = self.bucket.blob(f'index/{video_id}/embeddings.json')
            embeddings_blob.upload_from_string(
                json.dumps(embeddings, indent=2),
                content_type='application/json'
            )

            logger.info(f"Indexing complete for {video_id}: {len(shots)} shots")
            return index_doc

    def index_all_videos(self):
        """Index all videos in gs://bucket/videos/"""
        videos = self.list_videos()

        results = []
        for video_path in videos:
            try:
                full_path = f'gs://{self.bucket_name}/{video_path}'
                result = self.index_video(full_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to index {video_path}: {e}", exc_info=True)

        logger.info(f"Indexed {len(results)}/{len(videos)} videos successfully")
        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Index videos in GCS')
    parser.add_argument('--project-id', required=True, help='GCP project ID')
    parser.add_argument('--bucket-name', required=True, help='GCS bucket name')
    parser.add_argument('--video-path', help='Specific video to index (optional)')

    args = parser.parse_args()

    indexer = VideoIndexer(args.project_id, args.bucket_name)

    if args.video_path:
        # Index specific video
        result = indexer.index_video(args.video_path)
        print(json.dumps(result, indent=2))
    else:
        # Index all videos
        results = indexer.index_all_videos()
        print(f"Indexed {len(results)} videos")


if __name__ == '__main__':
    main()
