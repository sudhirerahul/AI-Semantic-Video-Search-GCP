'use client'

import { useState } from 'react'

export default function LeftHistoryPanel({ videos, selectedVideo, onSelectVideo, history, onSelectHistory }) {
  const [showVideos, setShowVideos] = useState(true)

  return (
    <div className="w-[270px] border-r border-brand-border bg-brand-dark flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-brand-border">
        <button
          onClick={() => window.location.reload()}
          className="w-full px-3 py-2 rounded-md bg-brand-accent-primary hover:bg-brand-accent-hover text-white font-medium transition-all duration-150 ease-smooth text-xs tracking-tight"
        >
          New conversation
        </button>
      </div>

      {/* Tabs - control console modes */}
      <div className="flex border-b border-brand-border bg-brand-dark">
        <button
          onClick={() => setShowVideos(true)}
          className={`relative flex-1 px-4 py-3 text-[13px] tracking-tighter transition-all duration-150 ${
            showVideos
              ? 'text-brand-text-primary font-semibold'
              : 'text-brand-text-secondary font-medium hover:text-brand-text-primary/80'
          }`}
        >
          Videos
          {showVideos && (
            <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-brand-accent-primary" />
          )}
        </button>
        <button
          onClick={() => setShowVideos(false)}
          className={`relative flex-1 px-4 py-3 text-[13px] tracking-tighter transition-all duration-150 ${
            !showVideos
              ? 'text-brand-text-primary font-semibold'
              : 'text-brand-text-secondary font-medium hover:text-brand-text-primary/80'
          }`}
        >
          History
          {!showVideos && (
            <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-brand-accent-primary" />
          )}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {showVideos ? (
          <div className="p-2 space-y-1">
            {videos ? (
              videos.map((video) => (
                <button
                  key={video.video_id}
                  onClick={() => onSelectVideo(video)}
                  className={`w-full p-3 rounded-md text-left transition-all duration-150 ease-smooth ${
                    selectedVideo?.video_id === video.video_id
                      ? 'bg-brand-hover'
                      : 'hover:bg-brand-hover/50'
                  }`}
                >
                  <div className="text-xs font-medium text-brand-text-primary mb-1 tracking-tight">
                    {video.title}
                  </div>
                  <div className="text-[11px] text-brand-text-tertiary tracking-tight">
                    {video.num_shots} scenes • {Math.floor(video.duration / 60)}m {Math.floor(video.duration % 60)}s
                  </div>
                </button>
              ))
            ) : (
              <div className="p-4 space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="w-full h-16 rounded-md bg-brand-surface animate-skeleton border border-brand-border" />
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {history.length > 0 ? (
              history.map((entry) => (
                <button
                  key={entry.id}
                  onClick={() => onSelectHistory(entry)}
                  className="w-full p-3 rounded-lg text-left hover:bg-brand-hover/50 transition-colors group"
                >
                  <div className="text-sm text-brand-text-primary mb-1 line-clamp-2">
                    {entry.query}
                  </div>
                  <div className="text-xs text-brand-text-tertiary">
                    {new Date(entry.timestamp).toLocaleDateString()}
                  </div>
                </button>
              ))
            ) : (
              <div className="p-4 text-center text-brand-text-tertiary text-sm">
                No history yet
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
