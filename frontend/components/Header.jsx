'use client'

export default function Header() {
  return (
    <header className="h-14 border-b border-brand-border bg-brand-dark flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-brand-accent-primary flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="font-semibold text-brand-text-primary text-sm tracking-tight">AI Video Search</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="px-2.5 py-1 rounded-sm bg-brand-surface border border-brand-border">
          <span className="text-[11px] text-brand-text-tertiary tracking-tight font-medium">CLIP ViT-B-32</span>
        </div>
      </div>
    </header>
  )
}
