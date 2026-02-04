'use client'

export default function Header() {
  return (
    <header className="h-14 border-b border-brand-border bg-brand-surface/50 backdrop-blur-xl flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-accent-primary to-blue-500 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="font-semibold text-brand-text-primary">AI Video Search</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="px-3 py-1.5 rounded-lg bg-brand-surface border border-brand-border">
          <span className="text-sm text-brand-text-secondary">CLIP ViT-B-32</span>
        </div>
      </div>
    </header>
  )
}
