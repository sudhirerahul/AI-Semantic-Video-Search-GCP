'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import Header from '../components/Header'
import LeftHistoryPanel from '../components/LeftHistoryPanel'
import ChatArea from '../components/ChatArea'
import VideoPlayerPanel from '../components/VideoPlayerPanel'
import { getVideos } from '../lib/api'

export default function Home() {
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [history, setHistory] = useState([])
  const [messages, setMessages] = useState([])
  const [currentClip, setCurrentClip] = useState(null)

  // Fetch videos
  const { data: videos, error: videosError } = useSWR('videos', getVideos)

  // Initialize with first video
  useEffect(() => {
    if (videos && videos.length > 0 && !selectedVideo) {
      setSelectedVideo(videos[0])
    }
  }, [videos, selectedVideo])

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('queryHistory')
    if (saved) {
      try {
        setHistory(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load history', e)
      }
    }
  }, [])

  // Save history to localStorage
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('queryHistory', JSON.stringify(history))
    }
  }, [history])

  const addToHistory = (query, videoId, results) => {
    const newEntry = {
      id: Date.now(),
      query,
      videoId,
      timestamp: new Date().toISOString(),
      results: results.slice(0, 1), // Save top result
    }
    setHistory(prev => [newEntry, ...prev].slice(0, 20)) // Keep last 20
  }

  const loadFromHistory = (entry) => {
    // Find video
    const video = videos?.find(v => v.video_id === entry.videoId)
    if (video) {
      setSelectedVideo(video)
    }

    // Rebuild messages
    const userMessage = {
      role: 'user',
      content: entry.query,
      timestamp: entry.timestamp,
    }
    const assistantMessage = {
      role: 'assistant',
      content: entry.results,
      timestamp: entry.timestamp,
    }
    setMessages([userMessage, assistantMessage])
  }

  return (
    <div className="h-screen flex flex-col bg-brand-dark">
      <Header />

      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar */}
        <LeftHistoryPanel
          videos={videos}
          selectedVideo={selectedVideo}
          onSelectVideo={setSelectedVideo}
          history={history}
          onSelectHistory={loadFromHistory}
        />

        {/* Main chat area */}
        <ChatArea
          selectedVideo={selectedVideo}
          messages={messages}
          onMessagesChange={setMessages}
          onAddToHistory={addToHistory}
          onPlayClip={setCurrentClip}
        />

        {/* Right panel - video player */}
        <VideoPlayerPanel
          clip={currentClip}
          onClose={() => setCurrentClip(null)}
        />
      </div>
    </div>
  )
}
