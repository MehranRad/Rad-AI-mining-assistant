'use client'

import { ChatMessage as ChatMessageType } from '@/lib/types'
import { TechnicalDetails } from './technical-details'
import { AlertTriangle } from 'lucide-react'

const ERROR_PREFIXES = ['خطا', 'متاسفانه']

function isError(text: string) {
  return ERROR_PREFIXES.some((p) => text.trim().startsWith(p))
}

export function ChatMessageItem({
  message,
  showTechnical,
}: {
  message: ChatMessageType
  showTechnical: boolean
}) {
  const isUser = message.role === 'user'
  const errored = !isUser && isError(message.content)

  return (
    <div className="flex justify-start" dir="rtl">
      <div className={`flex gap-3 max-w-[85%] md:max-w-[70%] ${isUser ? 'mr-auto flex-row-reverse' : ''}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-en font-bold ${
            isUser
              ? 'bg-neutral-800 text-neutral-300'
              : 'bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] text-white shadow-[0_0_15px_-3px_rgba(224,138,79,0.6)]'
          }`}
        >
          {isUser ? 'U' : 'R'}
        </div>

        <div
          className={`rounded-xl px-4 py-3 text-sm leading-7 ${
            isUser
              ? 'bg-[#E08A4F]/10 border border-[#E08A4F]/25 text-neutral-100'
              : errored
              ? 'bg-red-500/10 border border-red-500/25 text-neutral-100'
              : 'bg-neutral-900/70 border border-neutral-800 text-neutral-100'
          }`}
        >
          {errored && (
            <div className="flex items-center gap-1.5 text-red-400 text-xs font-medium mb-2">
              <AlertTriangle size={13} />
              خطا در پردازش
            </div>
          )}
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
          {!isUser && showTechnical && <TechnicalDetails steps={message.steps} />}
        </div>
      </div>
    </div>
  )
}