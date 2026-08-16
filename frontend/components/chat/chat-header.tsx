'use client'

import { Menu } from 'lucide-react'

type ChatHeaderProps = {
  showTechnical: boolean
  onToggleTechnical: (v: boolean) => void
  onOpenSidebar: () => void
}

export function ChatHeader({ showTechnical, onToggleTechnical, onOpenSidebar }: ChatHeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-4 md:px-6 py-4 border-b border-neutral-800/80 bg-neutral-950/40 backdrop-blur-sm"
      dir="rtl"
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="md:hidden w-9 h-9 -mr-1 flex items-center justify-center rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-900 transition-colors"
          aria-label="باز کردن منو"
        >
          <Menu size={20} />
        </button>

        <div className="relative w-8 h-8 rounded-full bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] flex items-center justify-center shadow-[0_0_15px_-3px_rgba(224,138,79,0.6)]">
          <span className="font-en text-white text-[10px] font-bold">R</span>
          <span className="absolute -bottom-0.5 -left-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-neutral-950" />
        </div>
        <div>
          <p className="font-en text-white text-sm font-semibold leading-none">Rad AI</p>
          <p className="text-[11px] text-neutral-500 mt-1 hidden sm:block">آماده پاسخگویی · معدن مس</p>
        </div>
      </div>

      <label className="flex items-center gap-2 text-xs text-neutral-400 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={showTechnical}
          onChange={(e) => onToggleTechnical(e.target.checked)}
          className="accent-[#B5723A] w-3.5 h-3.5"
        />
        <span className="hidden sm:inline">نمایش جزئیات فنی</span>
      </label>
    </header>
  )
}