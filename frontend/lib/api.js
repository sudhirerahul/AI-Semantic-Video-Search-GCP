/**
 * API wrapper for backend video search endpoints
 * Handles timeouts, errors, and provides typed responses
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export const fetchWithTimeout = async (url, opts = {}, timeout = 20000) => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    clearTimeout(id);

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }

    return res.json();
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }
    throw error;
  }
};

/**
 * GET /videos
 * Returns list of indexed videos with metadata
 */
export const getVideos = async () => {
  return fetchWithTimeout(`${API_BASE}/videos`);
};

/**
 * POST /query
 * Search for scenes using natural language
 */
export const queryScenes = async (video_id, query, top_k = 3) => {
  return fetchWithTimeout(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_id, query, top_k })
  });
};

/**
 * POST /extract_clip
 * Extract clip on-demand from cloud video
 * Longer timeout (45s) for clip generation
 */
export const extractClip = async (video_id, shot_index) => {
  return fetchWithTimeout(
    `${API_BASE}/extract_clip`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id, shot_index })
    },
    45000 // 45 second timeout for extraction
  );
};

/**
 * Format time in MM:SS format
 */
export const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Get score color class based on relevance
 */
export const getScoreColor = (score) => {
  if (score >= 0.25) return 'text-green-400';
  if (score >= 0.20) return 'text-yellow-400';
  return 'text-gray-400';
};
