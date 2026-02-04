#!/usr/bin/env python3
"""
FAISS Index Builder for Level 3 Advanced Video Search

Builds a FAISS index from video chunk embeddings stored in GCS.
Supports multiple videos and incremental updates.
"""

import os
import sys
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import tempfile

from google.cloud import storage


class FAISSIndexBuilder:
    """Build and manage FAISS index for video chunk embeddings."""

    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)

    def list_index_files(self) -> List[str]:
        """List all index JSON files in GCS bucket."""
        print("📂 Listing index files from GCS...")

        blobs = self.bucket.list_blobs(prefix='index/')
        index_files = []

        for blob in blobs:
            if blob.name.endswith('_index.json'):
                index_files.append(f"gs://{self.bucket_name}/{blob.name}")

        print(f"✅ Found {len(index_files)} index files")
        return index_files

    def load_index_file(self, index_uri: str) -> Dict[str, Any]:
        """Load index JSON from GCS."""
        # Parse GCS URI
        path_parts = index_uri[5:].split('/', 1)  # Remove gs://
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Download and parse
        content = blob.download_as_text()
        return json.loads(content)

    def extract_embeddings_and_metadata(
        self,
        index_files: List[str]
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Extract embeddings and metadata from all index files.

        Returns:
            embeddings: numpy array of shape (N, embedding_dim)
            metadata: list of metadata dicts for each chunk
        """
        print(f"\n🔍 Extracting embeddings from {len(index_files)} index files...")

        all_embeddings = []
        all_metadata = []

        for idx, index_uri in enumerate(index_files):
            print(f"   [{idx+1}/{len(index_files)}] Loading {index_uri.split('/')[-1]}")

            index_data = self.load_index_file(index_uri)

            video_id = index_data['video_id']
            chunks = index_data.get('chunks', [])

            for chunk in chunks:
                # Extract embedding
                embedding = np.array(chunk['embedding'], dtype=np.float32)
                all_embeddings.append(embedding)

                # Store metadata (without embedding to save memory)
                metadata = {
                    'video_id': video_id,
                    'video_name': index_data.get('video_name', ''),
                    'video_uri': index_data.get('video_uri', ''),
                    'chunk_global_id': chunk['chunk_global_id'],
                    'scene_id': chunk['scene_id'],
                    'chunk_id': chunk['chunk_id'],
                    'start_time': chunk['start_time'],
                    'end_time': chunk['end_time'],
                    'duration': chunk['duration'],
                    'thumbnail_uri': chunk['thumbnail_uri'],
                    'clip_uri': chunk['clip_uri'],
                    'description': chunk.get('description', ''),
                }
                all_metadata.append(metadata)

        embeddings = np.vstack(all_embeddings).astype(np.float32)

        print(f"✅ Extracted {len(all_embeddings)} embeddings")
        print(f"   Shape: {embeddings.shape}")
        print(f"   Dtype: {embeddings.dtype}")

        return embeddings, all_metadata

    def build_faiss_index(
        self,
        embeddings: np.ndarray,
        use_gpu: bool = False
    ) -> faiss.Index:
        """
        Build FAISS index from embeddings.

        For prototype, we use IndexFlatIP (inner product) which is:
        - Exact search (no approximation)
        - Fast for <100k vectors
        - No training required

        For production with millions of vectors, consider:
        - IndexIVFFlat (faster, approximate)
        - IndexHNSW (graph-based, very fast)
        """
        print(f"\n🏗️  Building FAISS index...")

        embedding_dim = embeddings.shape[1]
        num_vectors = embeddings.shape[0]

        print(f"   Embedding dimension: {embedding_dim}")
        print(f"   Number of vectors: {num_vectors}")

        # Normalize embeddings for cosine similarity
        # (our embeddings are already normalized in ingestion, but double-check)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / (norms + 1e-8)

        # Build flat index (exact search)
        # IndexFlatIP = Inner Product (equivalent to cosine similarity for normalized vectors)
        index = faiss.IndexFlatIP(embedding_dim)

        # Add vectors to index
        index.add(embeddings_normalized)

        print(f"✅ FAISS index built successfully")
        print(f"   Index type: {type(index).__name__}")
        print(f"   Total vectors: {index.ntotal}")
        print(f"   Is trained: {index.is_trained}")

        return index

    def save_index(
        self,
        index: faiss.Index,
        metadata: List[Dict[str, Any]],
        output_dir: str
    ) -> Tuple[str, str]:
        """
        Save FAISS index and metadata to disk.

        Returns:
            index_path: path to FAISS index file
            metadata_path: path to metadata JSON file
        """
        print(f"\n💾 Saving index to {output_dir}...")

        os.makedirs(output_dir, exist_ok=True)

        # Save FAISS index
        index_path = os.path.join(output_dir, 'video_chunks.faiss')
        faiss.write_index(index, index_path)

        # Save metadata
        metadata_path = os.path.join(output_dir, 'video_chunks_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                'total_chunks': len(metadata),
                'embedding_dim': index.d,
                'index_type': type(index).__name__,
                'chunks': metadata
            }, f, indent=2)

        print(f"✅ Index saved:")
        print(f"   FAISS index: {index_path}")
        print(f"   Metadata: {metadata_path}")

        # Print file sizes
        index_size = os.path.getsize(index_path) / (1024 * 1024)
        metadata_size = os.path.getsize(metadata_path) / (1024 * 1024)

        print(f"   Index size: {index_size:.2f} MB")
        print(f"   Metadata size: {metadata_size:.2f} MB")

        return index_path, metadata_path

    def upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """Upload file to GCS."""
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        uri = f"gs://{self.bucket_name}/{gcs_path}"
        print(f"   Uploaded to {uri}")
        return uri

    def build_and_save(self, output_dir: str = None, upload_to_gcs: bool = True):
        """
        Main pipeline: build FAISS index from all videos and save.

        Steps:
        1. List all index files in GCS
        2. Extract embeddings and metadata
        3. Build FAISS index
        4. Save locally
        5. Optionally upload to GCS
        """
        print(f"\n{'='*70}")
        print(f"🚀 Building FAISS Index for Video Search")
        print(f"{'='*70}\n")

        # Step 1: List index files
        index_files = self.list_index_files()

        if not index_files:
            print("❌ No index files found. Run ingestion first.")
            return None

        # Step 2: Extract embeddings
        embeddings, metadata = self.extract_embeddings_and_metadata(index_files)

        # Step 3: Build FAISS index
        faiss_index = self.build_faiss_index(embeddings)

        # Step 4: Save locally
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='faiss_index_')

        index_path, metadata_path = self.save_index(faiss_index, metadata, output_dir)

        # Step 5: Upload to GCS
        if upload_to_gcs:
            print(f"\n☁️  Uploading to GCS...")
            index_gcs_uri = self.upload_to_gcs(index_path, 'search_index/video_chunks.faiss')
            metadata_gcs_uri = self.upload_to_gcs(metadata_path, 'search_index/video_chunks_metadata.json')

            print(f"\n✅ Index uploaded to GCS:")
            print(f"   {index_gcs_uri}")
            print(f"   {metadata_gcs_uri}")

        print(f"\n{'='*70}")
        print(f"✅ FAISS Index Build Complete!")
        print(f"{'='*70}")
        print(f"📊 Statistics:")
        print(f"   Total videos: {len(index_files)}")
        print(f"   Total chunks: {len(metadata)}")
        print(f"   Embedding dimension: {embeddings.shape[1]}")
        print(f"   Index size: {os.path.getsize(index_path) / (1024 * 1024):.2f} MB")
        print(f"\n🔍 Ready for search!\n")

        return {
            'index_path': index_path,
            'metadata_path': metadata_path,
            'total_chunks': len(metadata),
            'total_videos': len(index_files)
        }


def main():
    """Main entry point for index builder."""

    PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', './faiss_index')

    builder = FAISSIndexBuilder(
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME
    )

    result = builder.build_and_save(
        output_dir=OUTPUT_DIR,
        upload_to_gcs=True
    )

    if result:
        print(f"\n✅ Index builder completed successfully!")
        print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ Index builder failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
