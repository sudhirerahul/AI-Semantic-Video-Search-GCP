'use client'

import { useState, useRef, useEffect } from 'react'
import { queryScenes } from '../lib/api'
import SceneCard from './SceneCard'

export default function ChatArea({ selectedVideo, messages, onMessagesChange, onAddToHistory, onPlayClip }) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const query = input.trim()

    if (!query || !selectedVideo || isLoading) return

    // Add user message
    const userMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }
    onMessagesChange([...messages, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Query backend
      const results = await queryScenes(selectedVideo.video_id, query, 3)

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: results,
        timestamp: new Date().toISOString(),
      }
      onMessagesChange([...messages, userMessage, assistantMessage])

      // Add to history
      onAddToHistory(query, selectedVideo.video_id, results)
    } catch (error) {
      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: 'error',
        error: error.message || 'Failed to search. Please try again.',
        timestamp: new Date().toISOString(),
      }
      onMessagesChange([...messages, userMessage, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <h2 className="text-lg font-semibold text-brand-text-primary mb-2 tracking-tight">
                  {selectedVideo ? `Search: ${selectedVideo.title}` : 'Select a video to start'}
                </h2>
                <p className="text-sm text-brand-text-secondary mb-6 leading-relaxed">
                  Enter natural language queries to find specific scenes
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {['person speaking', 'outdoor scene', 'close up shot', 'two people talking'].map((example) => (
                    <button
                      key={example}
                      onClick={() => setInput(example)}
                      className="px-3 py-1.5 rounded-md bg-brand-surface border border-brand-border hover:border-brand-accent-primary text-xs text-brand-text-secondary hover:text-brand-text-primary transition-all duration-150 ease-smooth"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                {message.role === 'user' ? (
                  <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-brand-accent-primary text-white">
                    {message.content}
                  </div>
                ) : message.content === 'error' ? (
                  <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400">
                    {message.error}
                  </div>
                ) : Array.isArray(message.content) && message.content.length === 0 ? (
                  <div className="max-w-[70%] px-4 py-3 rounded-2xl bg-brand-surface text-brand-text-secondary">
                    No matching scenes found. Try rephrasing your query.
                  </div>
                ) : (
                  <div className="w-full space-y-3">
                    <div className="text-brand-text-secondary text-sm">Found {message.content.length} matching scenes</div>
                    <div className="grid grid-cols-1 gap-3">
                      {message.content.map((scene, idx) => (
                        <SceneCard
                          key={idx}
                          scene={scene}
                          videoId={selectedVideo?.video_id}
                          onPlay={onPlayClip}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex justify-start animate-fade-in">
              <div className="space-y-3 w-full max-w-2xl">
                <div className="text-brand-text-secondary text-xs tracking-tight">Searching scenes...</div>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="w-full h-24 rounded-md bg-brand-surface animate-skeleton border border-brand-border" />
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-brand-border bg-brand-dark">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedVideo ? "Search for scenes..." : "Select a video first"}
              disabled={!selectedVideo || isLoading}
              className="w-full px-4 py-2.5 pr-12 rounded-md bg-brand-surface border border-brand-border focus:border-brand-accent-primary focus:outline-none text-brand-text-primary text-sm placeholder-brand-text-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 ease-smooth tracking-tight"
            />
            <button
              type="submit"
              disabled={!input.trim() || !selectedVideo || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md bg-brand-accent-primary hover:bg-brand-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 ease-smooth"
            >
              {isLoading ? (
                <svg className="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
