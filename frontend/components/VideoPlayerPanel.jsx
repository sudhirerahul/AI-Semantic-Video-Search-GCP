'use client'

import { formatTime } from '../lib/api'

export default function VideoPlayerPanel({ clip, onClose }) {
  if (!clip) {
    return (
      <div className="w-[420px] flex-shrink-0 border-l border-brand-border bg-brand-dark flex items-center justify-center">
        <div className="text-center px-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-brand-surface flex items-center justify-center">
            <svg className="w-8 h-8 text-brand-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-brand-text-primary mb-2 tracking-tight">
            No clip playing
          </h3>
          <p className="text-[13px] text-brand-text-secondary tracking-tight">
            Search for scenes and click Play to view clips
          </p>
        </div>
      </div>
    )
  }

  const expiresAt = new Date(clip.expires_at)
  const now = new Date()
  const minutesUntilExpiry = Math.floor((expiresAt - now) / 1000 / 60)

  return (
    <div className="w-[420px] flex-shrink-0 border-l border-brand-border bg-brand-dark flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-brand-border">
        <h2 className="text-xs font-semibold text-brand-text-primary tracking-tight">
          Clip Player
        </h2>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-brand-surface rounded-md transition-all duration-150 ease-smooth"
          aria-label="Close player"
        >
          <svg className="w-4 h-4 text-brand-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Video Player */}
      <div className="flex-1 flex flex-col overflow-y-auto scrollbar-thin">
        <div className="p-4 space-y-4">
          {/* Video */}
          <div className="relative bg-black rounded-md overflow-hidden">
            <video
              key={clip.clip_url}
              src={clip.clip_url}
              controls
              autoPlay
              className="w-full aspect-video"
            />
          </div>

          {/* Metadata */}
          <div className="space-y-2">
            {/* Time info */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-brand-text-secondary tracking-tight">Duration:</span>
              <span className="text-brand-text-primary font-medium tracking-tight">
                {clip.duration.toFixed(2)}s
              </span>
              <span className="text-brand-text-tertiary text-[11px] tracking-tight">
                ({formatTime(clip.start)} - {formatTime(clip.end)})
              </span>
            </div>

            {/* Shot info */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-brand-text-secondary tracking-tight">Shot:</span>
              <span className="text-brand-text-primary font-medium tracking-tight">
                {clip.shot_index}
              </span>
            </div>

            {/* Expiry notice */}
            <div className={`px-2.5 py-2 rounded-md border ${
              minutesUntilExpiry < 10
                ? 'bg-red-500/10 border-red-500/20'
                : 'bg-brand-surface border-brand-border'
            }`}>
              <div className="flex items-start gap-2">
                <svg className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${
                  minutesUntilExpiry < 10 ? 'text-red-400' : 'text-brand-text-tertiary'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <div className={`text-[11px] font-medium tracking-tight ${
                    minutesUntilExpiry < 10 ? 'text-red-400' : 'text-brand-text-secondary'
                  }`}>
                    {minutesUntilExpiry < 10 ? 'Expiring soon' : 'Temporary link'}
                  </div>
                  <div className="text-[10px] text-brand-text-tertiary mt-0.5 tracking-tight">
                    {minutesUntilExpiry > 0
                      ? `Valid for ${minutesUntilExpiry} more minutes`
                      : 'Link expired'
                    }
                  </div>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2">
              <a
                href={clip.clip_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-brand-dark hover:bg-brand-surface border border-brand-border hover:border-brand-accent-primary text-brand-text-primary text-sm font-medium rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span>Open in tab</span>
              </a>

              <a
                href={clip.clip_url}
                download={`clip_${clip.video_id}_shot_${clip.shot_index}.mp4`}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-brand-dark hover:bg-brand-surface border border-brand-border hover:border-brand-accent-primary text-brand-text-primary text-sm font-medium rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download</span>
              </a>
            </div>

            {/* Video ID (for debugging) */}
            <div className="text-xs text-brand-text-tertiary">
              Video: {clip.video_id}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
