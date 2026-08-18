import { ShiningText } from '@/components/ui/shining-text'

export function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-3 py-2" role="status" aria-live="polite">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] flex items-center justify-center shrink-0 shadow-[0_0_15px_-2px_rgba(224,138,79,0.6)]">
        <span className="font-en text-white text-[10px] font-bold">R</span>
      </div>
      <ShiningText text="در حال فکر کردن..." />
    </div>
  )
}