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
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-brand-text-primary mb-2">
                  {selectedVideo ? `Search "${selectedVideo.title}"` : 'Select a video to start'}
                </h2>
                <p className="text-brand-text-secondary">
                  Ask questions about scenes in natural language
                </p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center">
                  {['person speaking', 'outdoor scene', 'close up shot', 'two people talking'].map((example) => (
                    <button
                      key={example}
                      onClick={() => setInput(example)}
                      className="px-4 py-2 rounded-lg bg-brand-surface border border-brand-border hover:border-brand-accent-primary text-sm text-brand-text-secondary hover:text-brand-text-primary transition-colors"
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
              <div className="space-y-3">
                <div className="text-brand-text-secondary text-sm">Searching...</div>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="w-full max-w-md h-32 rounded-xl bg-brand-surface animate-pulse" />
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-brand-border bg-brand-surface/50 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedVideo ? "Search for scenes..." : "Select a video first"}
              disabled={!selectedVideo || isLoading}
              className="w-full px-4 py-3 pr-12 rounded-xl bg-brand-dark border border-brand-border focus:border-brand-accent-primary focus:outline-none text-brand-text-primary placeholder-brand-text-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            />
            <button
              type="submit"
              disabled={!input.trim() || !selectedVideo || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-brand-accent-primary hover:bg-brand-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
