'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { StepDetail } from '@/lib/types'

export function TechnicalDetails({ steps }: { steps?: StepDetail[] }) {
  const [open, setOpen] = useState(false)
  if (!steps || steps.length === 0) return null

  return (
    <div className="mt-3 border border-neutral-800 rounded-lg bg-neutral-950/60 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls="technical-details-panel"
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-neutral-400 hover:text-neutral-200 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
      >
        جزئیات فنی
        <ChevronDown size={14} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div id="technical-details-panel" className="px-3 pb-3 space-y-3">
          {steps.map((step, i) => (
            <div key={i} className="space-y-1.5">
              <p className="text-xs font-medium text-neutral-300">
                {i + 1}. {step.label}
              </p>
              <pre
                className="text-[11px] bg-black/50 border border-neutral-800 rounded-md p-2.5 overflow-x-auto text-[#E08A4F] font-en"
                dir="ltr"
              >
                {step.sql}
              </pre>
              <p className="text-[11px] text-neutral-500 whitespace-pre-wrap break-words">
                {step.result?.slice(0, 1000)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}