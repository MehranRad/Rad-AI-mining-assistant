'use client'

import { useState, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

type ChatInputProps = {
  onSend: (text: string) => void
  disabled: boolean
}

export function ChatInputBar({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="p-4 border-t border-neutral-800/80 bg-neutral-950/40 backdrop-blur-sm" dir="rtl">
      <div className="flex items-end gap-2 max-w-4xl mx-auto bg-neutral-900/80 border border-neutral-700 rounded-xl px-3 py-2 focus-within:border-[#E08A4F]/70 focus-within:shadow-[0_0_0_3px_rgba(224,138,79,0.15)] transition-all">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="درباره تولید، تجهیزات، نیروی انسانی یا عملکرد معدن بپرسید..."
          dir="rtl"
          className="flex-1 bg-transparent resize-none outline-none text-sm text-white placeholder:text-neutral-500 py-1.5 max-h-32 disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          className="shrink-0 w-9 h-9 rounded-lg bg-[#B5723A] hover:bg-[#8B4A28] disabled:opacity-40 disabled:hover:bg-[#B5723A] flex items-center justify-center transition-colors"
        >
          <Send size={16} className="text-white -rotate-90" />
        </button>
      </div>
      <p className="font-en text-[10px] text-neutral-600 text-center mt-2">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}