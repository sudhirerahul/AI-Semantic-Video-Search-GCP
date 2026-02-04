#!/usr/bin/env python3
"""
Level 3 Advanced Video Search Service

Features:
- Multi-modal embeddings (CLIP)
- Two-stage retrieval (fast recall + reranking)
- Temporal merging (group adjacent chunks)
- Metadata filtering
- Signed URLs for clips
"""

import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from google.cloud import storage
from sentence_transformers import SentenceTransformer


class VideoSearchService:
    """Level 3 advanced video search with FAISS and CLIP."""

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        index_path: str,
        metadata_path: str,
        embedding_model: str = "clip-ViT-B-32"
    ):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)

        # Load FAISS index
        print(f"📂 Loading FAISS index from {index_path}")
        self.index = faiss.read_index(index_path)
        print(f"✅ Index loaded: {self.index.ntotal} vectors")

        # Load metadata
        print(f"📂 Loading metadata from {metadata_path}")
        with open(metadata_path, 'r') as f:
            metadata_obj = json.load(f)
            self.metadata = metadata_obj['chunks']
            self.total_chunks = metadata_obj['total_chunks']
            self.embedding_dim = metadata_obj['embedding_dim']
        print(f"✅ Metadata loaded: {self.total_chunks} chunks")

        # Load embedding model
        print(f"🤖 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        print(f"✅ Model loaded")

    def embed_query(self, query: str) -> np.ndarray:
        """Embed query text using CLIP."""
        embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def search_faiss(
        self,
        query_embedding: np.ndarray,
        k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Fast recall using FAISS.
        Returns top-K candidates.
        """
        # Reshape for FAISS (expects 2D array)
        query_vector = query_embedding.reshape(1, -1)

        # Search
        scores, indices = self.index.search(query_vector, k)

        # Build results
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['score'] = float(score)
                result['index_id'] = int(idx)
                results.append(result)

        return results

    def rerank_results(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Rerank candidates for better relevance.

        Level 3 reranking strategies:
        1. Boost by text similarity (description match)
        2. Penalize very short clips (<1s)
        3. Prefer chunks with high base score
        4. Consider temporal coherence (adjacent chunks)
        """
        query_lower = query.lower()

        for candidate in candidates:
            base_score = candidate['score']

            # Text match boost
            description = candidate.get('description', '').lower()
            text_match = sum(word in description for word in query_lower.split())
            text_boost = text_match * 0.05  # +5% per matching word

            # Duration penalty for very short clips
            duration = candidate.get('duration', 0)
            duration_penalty = -0.1 if duration < 1.0 else 0

            # Final reranked score
            candidate['reranked_score'] = base_score + text_boost + duration_penalty
            candidate['text_boost'] = text_boost
            candidate['duration_penalty'] = duration_penalty

        # Sort by reranked score
        reranked = sorted(candidates, key=lambda x: x['reranked_score'], reverse=True)

        return reranked[:top_k]

    def temporal_merge(
        self,
        results: List[Dict[str, Any]],
        max_gap: float = 1.0,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Stage 3: Temporal merging (Level 3 feature).

        Group adjacent high-scoring chunks into natural scenes.

        Args:
            max_gap: Maximum time gap (seconds) between chunks to merge
            min_score: Minimum score to consider for merging
        """
        if not results:
            return []

        # Group by video_id
        by_video = defaultdict(list)
        for result in results:
            if result.get('reranked_score', 0) >= min_score:
                by_video[result['video_id']].append(result)

        merged_results = []

        for video_id, chunks in by_video.items():
            # Sort by start_time
            chunks_sorted = sorted(chunks, key=lambda x: x['start_time'])

            # Merge adjacent chunks
            merged_groups = []
            current_group = [chunks_sorted[0]]

            for chunk in chunks_sorted[1:]:
                last_chunk = current_group[-1]

                # Check if adjacent (within max_gap)
                time_gap = chunk['start_time'] - last_chunk['end_time']

                if time_gap <= max_gap:
                    # Merge into current group
                    current_group.append(chunk)
                else:
                    # Start new group
                    merged_groups.append(current_group)
                    current_group = [chunk]

            # Add last group
            if current_group:
                merged_groups.append(current_group)

            # Create merged result for each group
            for group in merged_groups:
                # Calculate merged metadata
                merged = {
                    'video_id': video_id,
                    'video_name': group[0]['video_name'],
                    'video_uri': group[0]['video_uri'],
                    'start_time': group[0]['start_time'],
                    'end_time': group[-1]['end_time'],
                    'duration': group[-1]['end_time'] - group[0]['start_time'],
                    'num_chunks': len(group),
                    'avg_score': np.mean([c['reranked_score'] for c in group]),
                    'max_score': max(c['reranked_score'] for c in group),
                    'thumbnail_uri': group[0]['thumbnail_uri'],  # Use first chunk's thumbnail
                    'clip_uri': group[0]['clip_uri'],  # Use first chunk's clip (for now)
                    'chunks': group,  # Include all chunks for reference
                    'merged': True
                }

                merged_results.append(merged)

        # Sort by score
        merged_results.sort(key=lambda x: x['max_score'], reverse=True)

        return merged_results

    def generate_signed_url(
        self,
        gcs_uri: str,
        expiration_minutes: int = 60
    ) -> str:
        """Generate signed URL for GCS object."""
        # Parse GCS URI
        path_parts = gcs_uri[5:].split('/', 1)  # Remove gs://
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Generate signed URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url

    def search(
        self,
        query: str,
        top_k: int = 10,
        recall_k: int = 50,
        enable_temporal_merge: bool = True,
        enable_signed_urls: bool = True,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Main search method with Level 3 features.

        Args:
            query: Search query text
            top_k: Number of final results to return
            recall_k: Number of candidates for stage 1 recall
            enable_temporal_merge: Whether to merge adjacent chunks
            enable_signed_urls: Whether to generate signed URLs
            min_score: Minimum score threshold

        Returns:
            Search results with metadata and URLs
        """
        print(f"\n🔍 Searching for: '{query}'")

        start_time = datetime.now()

        # Stage 1: Embed query
        query_embedding = self.embed_query(query)
        embed_time = (datetime.now() - start_time).total_seconds() * 1000

        # Stage 2: Fast recall with FAISS
        recall_start = datetime.now()
        candidates = self.search_faiss(query_embedding, k=recall_k)
        recall_time = (datetime.now() - recall_start).total_seconds() * 1000

        print(f"   📊 Stage 1 (Recall): {len(candidates)} candidates in {recall_time:.0f}ms")

        # Stage 3: Rerank
        rerank_start = datetime.now()
        reranked = self.rerank_results(query, candidates, top_k=recall_k)
        rerank_time = (datetime.now() - rerank_start).total_seconds() * 1000

        print(f"   📊 Stage 2 (Rerank): Top {len(reranked)} in {rerank_time:.0f}ms")

        # Stage 4: Temporal merge (optional)
        if enable_temporal_merge:
            merge_start = datetime.now()
            results = self.temporal_merge(reranked, min_score=min_score)
            merge_time = (datetime.now() - merge_start).total_seconds() * 1000
            print(f"   📊 Stage 3 (Merge): {len(results)} merged scenes in {merge_time:.0f}ms")
        else:
            results = reranked
            merge_time = 0

        # Filter by min_score
        results = [r for r in results if r.get('avg_score', r.get('reranked_score', 0)) >= min_score]

        # Limit to top_k
        results = results[:top_k]

        # Generate signed URLs
        if enable_signed_urls:
            url_start = datetime.now()
            for result in results:
                result['thumbnail_url'] = self.generate_signed_url(result['thumbnail_uri'])
                result['clip_url'] = self.generate_signed_url(result['clip_uri'])
            url_time = (datetime.now() - url_start).total_seconds() * 1000
            print(f"   📊 Stage 4 (URLs): {len(results)} signed URLs in {url_time:.0f}ms")
        else:
            url_time = 0

        total_time = (datetime.now() - start_time).total_seconds() * 1000

        print(f"   ✅ Total: {len(results)} results in {total_time:.0f}ms")

        return {
            'query': query,
            'total_results': len(results),
            'results': results,
            'timing': {
                'embedding_ms': embed_time,
                'recall_ms': recall_time,
                'rerank_ms': rerank_time,
                'merge_ms': merge_time,
                'signed_urls_ms': url_time,
                'total_ms': total_time
            },
            'stats': {
                'total_chunks_indexed': self.total_chunks,
                'candidates_recalled': len(candidates),
                'candidates_reranked': len(reranked),
                'results_returned': len(results)
            }
        }


def main():
    """Test search service locally."""
    PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0067393875')
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'gen-lang-client-0067393875-media-1770102442')

    # Paths to index files
    index_path = './faiss_index/video_chunks.faiss'
    metadata_path = './faiss_index/video_chunks_metadata.json'

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        print("❌ Index files not found. Run faiss_index_builder.py first.")
        return

    # Initialize search service
    service = VideoSearchService(
        project_id=PROJECT_ID,
        bucket_name=BUCKET_NAME,
        index_path=index_path,
        metadata_path=metadata_path
    )

    # Test queries
    test_queries = [
        "person walking",
        "outdoor scene",
        "conversation between two people",
        "close up shot",
        "action scene"
    ]

    print("\n" + "="*70)
    print("🧪 Testing Search Service")
    print("="*70)

    for query in test_queries:
        result = service.search(
            query=query,
            top_k=5,
            enable_temporal_merge=True,
            enable_signed_urls=False  # Skip for local testing
        )

        print(f"\n📊 Query: '{query}'")
        print(f"   Results: {result['total_results']}")
        print(f"   Time: {result['timing']['total_ms']:.0f}ms")

        for i, r in enumerate(result['results'][:3]):
            print(f"\n   [{i+1}] Score: {r.get('avg_score', r.get('reranked_score', 0)):.3f}")
            print(f"       Time: {r['start_time']:.1f}s - {r['end_time']:.1f}s")
            print(f"       Video: {r['video_name']}")
            if r.get('merged'):
                print(f"       Merged: {r['num_chunks']} chunks")


if __name__ == "__main__":
    main()
