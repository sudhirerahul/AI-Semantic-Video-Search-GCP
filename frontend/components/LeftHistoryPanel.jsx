'use client'

import { useState } from 'react'

export default function LeftHistoryPanel({ videos, selectedVideo, onSelectVideo, history, onSelectHistory }) {
  const [showVideos, setShowVideos] = useState(true)

  return (
    <div className="w-[270px] border-r border-brand-border bg-brand-surface flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-brand-border">
        <button
          onClick={() => window.location.reload()}
          className="w-full px-4 py-2.5 rounded-lg bg-brand-accent-primary hover:bg-brand-accent-hover text-white font-medium transition-colors text-sm"
        >
          New conversation
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-brand-border">
        <button
          onClick={() => setShowVideos(true)}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
            showVideos
              ? 'text-brand-text-primary border-b-2 border-brand-accent-primary'
              : 'text-brand-text-secondary hover:text-brand-text-primary'
          }`}
        >
          Videos
        </button>
        <button
          onClick={() => setShowVideos(false)}
          className={`flex-1 px-4 py-2.5 text-sm font-medium transition-colors ${
            !showVideos
              ? 'text-brand-text-primary border-b-2 border-brand-accent-primary'
              : 'text-brand-text-secondary hover:text-brand-text-primary'
          }`}
        >
          History
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
                  className={`w-full p-3 rounded-lg text-left transition-colors ${
                    selectedVideo?.video_id === video.video_id
                      ? 'bg-brand-hover'
                      : 'hover:bg-brand-hover/50'
                  }`}
                >
                  <div className="text-sm font-medium text-brand-text-primary mb-1">
                    {video.title}
                  </div>
                  <div className="text-xs text-brand-text-tertiary">
                    {video.num_shots} scenes • {Math.floor(video.duration / 60)}m {Math.floor(video.duration % 60)}s
                  </div>
                </button>
              ))
            ) : (
              <div className="p-4 text-center text-brand-text-tertiary text-sm">
                Loading videos...
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
