#!/usr/bin/env python3
"""
Level 3 Advanced Video Ingestion Worker
Processes videos with:
- Smart chunking (2-4 second segments)
- Multi-modal embeddings (visual + text)
- Metadata enrichment
- Scene detection and extraction
"""

import os
import sys
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.cloud import storage
from sentence_transformers import SentenceTransformer
import numpy as np


class VideoIngestionWorker:
    """Level 3 advanced video ingestion with chunking and multi-modal embeddings."""

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        embedding_model: str = "clip-ViT-B-32"
    ):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)

        print(f"🤖 Initializing embedding model: {embedding_model}")
        # Use CLIP for multi-modal (image + text) embeddings
        self.embedding_model = SentenceTransformer(embedding_model)
        print(f"✅ Model loaded successfully")

    def download_video(self, video_uri: str, local_path: str) -> str:
        """Download video from GCS to local path."""
        print(f"⬇️  Downloading video from {video_uri}")

        # Parse GCS URI
        if video_uri.startswith('gs://'):
            # Remove gs:// prefix and split bucket/path
            path_parts = video_uri[5:].split('/', 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1] if len(path_parts) > 1 else ''

            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.download_to_filename(local_path)
            print(f"✅ Video downloaded to {local_path}")
            return local_path
        else:
            raise ValueError(f"Invalid GCS URI: {video_uri}")

    def detect_scenes_ffmpeg(self, video_path: str, threshold: float = 0.3) -> List[Dict[str, float]]:
        """
        Detect scene changes using FFmpeg's scene detection.
        Returns list of scene boundaries with start/end times.

        Level 3: We use a lower threshold for more granular scenes.
        """
        print(f"🎬 Detecting scenes (threshold={threshold})...")

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', f'select=gt(scene\\,{threshold}),showinfo',
            '-f', 'null',
            '-'
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Parse scene change timestamps from ffmpeg output
        scene_times = [0.0]  # Always start with time 0

        for line in result.stdout.split('\n'):
            if 'pts_time:' in line:
                try:
                    # Extract timestamp from line like "pts_time:12.345"
                    time_str = line.split('pts_time:')[1].split()[0]
                    timestamp = float(time_str)
                    scene_times.append(timestamp)
                except (IndexError, ValueError):
                    continue

        # Get video duration
        duration = self._get_video_duration(video_path)
        scene_times.append(duration)

        # Remove duplicates and sort
        scene_times = sorted(list(set(scene_times)))

        # Create scene boundaries
        scenes = []
        for i in range(len(scene_times) - 1):
            scenes.append({
                'scene_id': i,
                'start_time': scene_times[i],
                'end_time': scene_times[i + 1],
                'duration': scene_times[i + 1] - scene_times[i]
            })

        print(f"✅ Detected {len(scenes)} scenes")
        return scenes

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())

    def chunk_scene(self, scene: Dict[str, Any], chunk_size: float = 3.0) -> List[Dict[str, Any]]:
        """
        Level 3: Break scene into smaller semantic chunks.
        Each chunk is 2-4 seconds for more granular search.
        """
        chunks = []
        start = scene['start_time']
        end = scene['end_time']
        duration = end - start

        # If scene is already small, don't chunk
        if duration <= chunk_size:
            return [{
                'chunk_id': 0,
                'start_time': start,
                'end_time': end,
                'duration': duration
            }]

        # Split into chunks
        current = start
        chunk_id = 0

        while current < end:
            chunk_end = min(current + chunk_size, end)
            chunks.append({
                'chunk_id': chunk_id,
                'start_time': current,
                'end_time': chunk_end,
                'duration': chunk_end - current
            })
            current = chunk_end
            chunk_id += 1

        return chunks

    def extract_thumbnail(
        self,
        video_path: str,
        timestamp: float,
        output_path: str
    ) -> str:
        """Extract a single frame thumbnail at given timestamp."""
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    def extract_clip(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """Extract a video clip segment."""
        duration = end_time - start_time

        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',
            '-y',
            output_path
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    def compute_embedding(self, text: str, image_path: Optional[str] = None) -> np.ndarray:
        """
        Level 3: Multi-modal embeddings.
        If image provided, use visual features. Otherwise, use text.
        CLIP model handles both.
        """
        if image_path and os.path.exists(image_path):
            # Image embedding using CLIP
            from PIL import Image
            image = Image.open(image_path)
            embedding = self.embedding_model.encode(image, convert_to_numpy=True)
        else:
            # Text embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    def upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """Upload file to GCS and return public URL."""
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        return f"gs://{self.bucket_name}/{gcs_path}"

    def process_video(self, video_uri: str) -> Dict[str, Any]:
        """
        Main processing pipeline (Level 3 Advanced).

        Steps:
        1. Download video
        2. Detect scenes
        3. Chunk scenes into 2-4 second segments
        4. Extract thumbnails per chunk
        5. Extract clips per chunk (optional)
        6. Generate multi-modal embeddings
        7. Build metadata index
        8. Upload to GCS
        """
        print(f"\n{'='*60}")
        print(f"🎯 Processing Video: {video_uri}")
        print(f"{'='*60}\n")

        video_name = video_uri.split('/')[-1].replace('.mp4', '')
        video_id = f"{video_name}_{uuid.uuid4().hex[:8]}"

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Download video
            video_path = os.path.join(tmpdir, 'video.mp4')
            self.download_video(video_uri, video_path)

            # 2. Detect scenes
            scenes = self.detect_scenes_ffmpeg(video_path, threshold=0.25)

            # 3. Process each scene with chunking
            index_data = {
                'video_id': video_id,
                'video_name': video_name,
                'video_uri': video_uri,
                'processed_at': datetime.utcnow().isoformat(),
                'total_scenes': len(scenes),
                'chunks': []
            }

            chunk_global_id = 0

            for scene in scenes:
                scene_id = scene['scene_id']
                print(f"\n📍 Processing Scene {scene_id}/{len(scenes)-1}")
                print(f"   Time: {scene['start_time']:.2f}s - {scene['end_time']:.2f}s")

                # Level 3: Chunk the scene
                chunks = self.chunk_scene(scene, chunk_size=3.0)
                print(f"   Chunks: {len(chunks)}")

                for chunk in chunks:
                    chunk_id = chunk['chunk_id']
                    start_time = chunk['start_time']
                    end_time = chunk['end_time']

                    # Mid-point for thumbnail
                    mid_time = (start_time + end_time) / 2

                    print(f"   └─ Chunk {chunk_id}: {start_time:.2f}s - {end_time:.2f}s")

                    # Extract thumbnail
                    thumb_filename = f"thumb_{video_id}_s{scene_id}_c{chunk_id}.jpg"
                    thumb_path = os.path.join(tmpdir, thumb_filename)
                    self.extract_thumbnail(video_path, mid_time, thumb_path)

                    # Upload thumbnail
                    thumb_gcs_path = f"thumbnails/{thumb_filename}"
                    thumb_uri = self.upload_to_gcs(thumb_path, thumb_gcs_path)

                    # Extract clip (optional, can be expensive)
                    clip_filename = f"clip_{video_id}_s{scene_id}_c{chunk_id}.mp4"
                    clip_path = os.path.join(tmpdir, clip_filename)
                    self.extract_clip(video_path, start_time, end_time, clip_path)

                    # Upload clip
                    clip_gcs_path = f"clips/{clip_filename}"
                    clip_uri = self.upload_to_gcs(clip_path, clip_gcs_path)

                    # Generate description for embedding
                    description = f"Video scene from {start_time:.1f}s to {end_time:.1f}s"

                    # Compute multi-modal embedding (using thumbnail)
                    embedding = self.compute_embedding(description, thumb_path)

                    # Build chunk metadata
                    chunk_data = {
                        'chunk_global_id': chunk_global_id,
                        'scene_id': scene_id,
                        'chunk_id': chunk_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time,
                        'thumbnail_uri': thumb_uri,
                        'clip_uri': clip_uri,
                        'description': description,
                        'embedding': embedding.tolist(),
                        'metadata': {
                            'video_id': video_id,
                            'scene_id': scene_id,
                            'chunk_id': chunk_id
                        }
                    }

                    index_data['chunks'].append(chunk_data)
                    chunk_global_id += 1

            # Save index to GCS
            index_filename = f"{video_id}_index.json"
            index_path = os.path.join(tmpdir, index_filename)

            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            index_gcs_path = f"index/{index_filename}"
            index_uri = self.upload_to_gcs(index_path, index_gcs_path)

            print(f"\n{'='*60}")
            print(f"✅ Processing Complete!")
            print(f"{'='*60}")
            print(f"📊 Total chunks: {len(index_data['chunks'])}")
            print(f"📁 Index: {index_uri}")
            print(f"🔍 Ready for search!\n")

            return {
                'video_id': video_id,
                'index_uri': index_uri,
                'total_chunks': len(index_data['chunks']),
                'total_scenes': len(scenes)
            }


def main():
    """Main entry point for worker."""
    if len(sys.argv) != 2:
        print("Usage: python ingest_worker.py gs://bucket-name/raw/video.mp4")
        sys.exit(1)

    video_uri = sys.argv[1]

    PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')

    worker = VideoIngestionWorker(
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME
    )

    result = worker.process_video(video_uri)

    print(f"\n✅ Worker completed successfully!")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
