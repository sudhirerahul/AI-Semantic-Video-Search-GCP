'use client'

import { useState } from 'react'
import { extractClip, formatTime, getScoreColor } from '../lib/api'

export default function SceneCard({ scene, videoId, onPlay }) {
  const [isExtracting, setIsExtracting] = useState(false)
  const [error, setError] = useState(null)

  const handlePlay = async () => {
    setIsExtracting(true)
    setError(null)

    try {
      const clipData = await extractClip(videoId, scene.shot_index)
      onPlay(clipData)
    } catch (err) {
      setError(err.message || 'Failed to extract clip')
    } finally {
      setIsExtracting(false)
    }
  }

  const duration = scene.end - scene.start
  const scoreColor = getScoreColor(scene.score)

  return (
    <div className="group relative bg-brand-surface border border-brand-border rounded-xl overflow-hidden hover:border-brand-accent-primary transition-colors">
      <div className="flex gap-4 p-4">
        {/* Thumbnail */}
        <div className="relative flex-shrink-0 w-40 h-24 bg-brand-dark rounded-lg overflow-hidden">
          {scene.thumbnail_url ? (
            <img
              src={scene.thumbnail_url}
              alt={`Scene at ${formatTime(scene.start)}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-brand-text-tertiary text-sm">
              No thumbnail
            </div>
          )}

          {/* Duration badge */}
          <div className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/80 backdrop-blur-sm rounded text-xs text-white font-medium">
            {duration.toFixed(1)}s
          </div>
        </div>

        {/* Metadata */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm text-brand-text-secondary">
                {formatTime(scene.start)} - {formatTime(scene.end)}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${scoreColor.bg} ${scoreColor.text}`}>
                {(scene.score * 100).toFixed(0)}% match
              </span>
            </div>

            <div className="text-xs text-brand-text-tertiary">
              Shot {scene.shot_index}
            </div>
          </div>

          {/* Play button */}
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={handlePlay}
              disabled={isExtracting}
              className="flex items-center gap-2 px-4 py-2 bg-brand-accent-primary hover:bg-brand-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
            >
              {isExtracting ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Extracting...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  <span>Play clip</span>
                </>
              )}
            </button>

            {error && (
              <span className="text-xs text-red-400">
                {error}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Hover effect overlay */}
      <div className="absolute inset-0 border-2 border-transparent group-hover:border-brand-accent-primary/20 rounded-xl pointer-events-none transition-colors" />
    </div>
  )
}
