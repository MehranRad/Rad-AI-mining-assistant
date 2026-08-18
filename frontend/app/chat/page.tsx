'use client'

import { useEffect, useRef, useState, useCallback, useSyncExternalStore } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '@/components/chat/sidebar'
import { ChatHeader } from '@/components/chat/chat-header'
import { ChatMessageItem } from '@/components/chat/chat-message'
import { ChatInputBar } from '@/components/chat/chat-input'
import { EmptyState } from '@/components/chat/empty-state'
import { KpiCards } from '@/components/chat/kpi-cards'
import { ThinkingIndicator } from '@/components/chat/thinking-indicator'
import { StoredUser, ChatMessage, StepDetail } from '@/lib/types'
import { askQuestionStream, createSession, saveMessage, loadMessages } from '@/lib/api'
import { ArrowDown, PanelLeft } from 'lucide-react'

let cachedUser: StoredUser | null = null
let cachedRaw: string | null | undefined

function subscribeUser() {
  return () => {}
}

function getUserSnapshot(): StoredUser | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem('rad_ai_user')
  if (raw !== cachedRaw) {
    cachedRaw = raw
    if (raw === null) {
      cachedUser = null
    } else {
      try {
        cachedUser = JSON.parse(raw)
      } catch {
        cachedUser = null
      }
    }
  }
  return cachedUser
}

function getServerSnapshot(): StoredUser | null {
  return null
}

export default function ChatPage() {
  const router = useRouter()
  const user = useSyncExternalStore(subscribeUser, getUserSnapshot, getServerSnapshot)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showTechnical, setShowTechnical] = useState(false)
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0)
  const [confidentialNotice, setConfidentialNotice] = useState(false)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('rad_ai_sidebar_collapsed') === '1'
  })
  const [isNearBottom, setIsNearBottom] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)
  const followRef = useRef(true)
  const scrollRafRef = useRef<number | null>(null)
  const SCROLL_THRESHOLD = 120

  const toggleSidebar = useCallback(() => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev
      if (typeof window !== 'undefined') {
        localStorage.setItem('rad_ai_sidebar_collapsed', next ? '1' : '0')
      }
      return next
    })
  }, [])

  const handleScroll = useCallback(() => {
    // Throttle with requestAnimationFrame so the near-bottom state is only
    // re-evaluated once per frame instead of once per scroll event.
    if (scrollRafRef.current !== null) return
    scrollRafRef.current = requestAnimationFrame(() => {
      scrollRafRef.current = null
      const el = scrollRef.current
      if (!el) return
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      const near = distanceFromBottom < SCROLL_THRESHOLD
      followRef.current = near
      setIsNearBottom((prev) => (prev === near ? prev : near))
    })
  }, [])

  useEffect(() => {
    return () => {
      if (scrollRafRef.current !== null) cancelAnimationFrame(scrollRafRef.current)
    }
  }, [])

  const scrollToLatest = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    followRef.current = true
    setIsNearBottom(true)
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [])

  useEffect(() => {
    if (!localStorage.getItem('rad_ai_user')) {
      router.push('/')
    }
  }, [router])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    // Only follow the conversation if the user is (or chose to be) at the
    // bottom — never force someone who scrolled up back to the latest token.
    if (followRef.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages])

  const handleNewConversation = useCallback(() => {
    followRef.current = true
    setIsNearBottom(true)
    setSessionId(null)
    setMessages([])
    setConfidentialNotice(false)
  }, [])

  const handleSelectSession = useCallback(
    async (id: string) => {
      if (!user) return
      const msgs = await loadMessages(user.user_id, id)
      followRef.current = true
      setIsNearBottom(true)
      setSessionId(id)
      setMessages(msgs)
      setConfidentialNotice(false)
    },
    [user]
  )

  const handleLogout = () => {
    localStorage.removeItem('rad_ai_user')
    localStorage.removeItem('rad_ai_token')
    router.push('/')
  }

  const handleSend = async (question: string) => {
    if (!user) return
    // Sending a message always returns the conversation to the bottom and
    // resumes auto-following, even if the user had scrolled up to read.
    followRef.current = true
    setIsNearBottom(true)
    const recentHistory = messages.slice(-3).map((m) => ({ role: m.role, content: m.content }))
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setIsLoading(true)
    setConfidentialNotice(false)

    let assistantIndex = -1
    let fullAnswer = ''
    let finalSteps: StepDetail[] = []
    let finalConfidential = false

    setMessages((prev) => {
      assistantIndex = prev.length
      return [...prev, { role: 'assistant', content: '' }]
    })

    await askQuestionStream(question, recentHistory, {
      onMeta: (steps, isConfidential) => {
        finalSteps = steps
        finalConfidential = isConfidential
      },
      onToken: (token) => {
        fullAnswer += token
        setIsLoading(false)
        setMessages((prev) => {
          const next = [...prev]
          next[assistantIndex] = { role: 'assistant', content: fullAnswer, steps: finalSteps }
          return next
        })
      },
      onDone: async () => {
        setConfidentialNotice(finalConfidential)
        if (!finalConfidential) {
          let activeSessionId = sessionId
          if (activeSessionId === null) {
            const created = await createSession(question)
            activeSessionId = created.session_id
            setSessionId(activeSessionId)
            setSidebarRefreshKey((k) => k + 1)
          }
          await saveMessage(activeSessionId!, 'user', question)
          await saveMessage(activeSessionId!, 'assistant', fullAnswer, finalSteps)
        }
      },
      onError: (message) => {
        setIsLoading(false)
        setMessages((prev) => {
          const next = [...prev]
          next[assistantIndex] = { role: 'assistant', content: `خطای غیرمنتظره رخ داد: ${message}` }
          return next
        })
      },
    })
  }

  if (!user) return null

  return (
    <div dir="rtl" className="h-screen w-full flex overflow-hidden">
      <Sidebar
        user={user}
        activeSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        refreshKey={sidebarRefreshKey}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
        collapsed={isSidebarCollapsed}
        onToggleSidebar={toggleSidebar}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <ChatHeader
          showTechnical={showTechnical}
          onToggleTechnical={setShowTechnical}
          onOpenSidebar={() => setIsMobileSidebarOpen(true)}
        />

        <div className="relative flex-1 min-h-0 overflow-hidden">
          {isSidebarCollapsed && (
            <button
              onClick={toggleSidebar}
              className="hidden md:flex absolute top-3 right-3 z-20 w-9 h-9 items-center justify-center rounded-full border border-neutral-700 bg-neutral-900/90 text-neutral-400 hover:text-white hover:border-[#E08A4F]/50 shadow-lg backdrop-blur-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
              aria-label="باز کردن نوار کناری"
              title="باز کردن نوار کناری"
            >
              <PanelLeft size={18} />
            </button>
          )}
          <div ref={scrollRef} onScroll={handleScroll} className="h-full overflow-y-auto px-4 md:px-8 py-6">
            <div className="max-w-3xl mx-auto">
              {messages.length === 0 && !isLoading && (
                <>
                  <KpiCards />
                  <EmptyState onPick={handleSend} />
                </>
              )}

              <div className="space-y-4">
                {messages.map((m, i) => (
                  <ChatMessageItem key={i} message={m} showTechnical={showTechnical} />
                ))}
                {isLoading && <ThinkingIndicator />}
              </div>

              {confidentialNotice && (
                <p className="text-xs text-neutral-500 mt-3 text-center">
                  🔒 این گفتگو شامل اطلاعات محرمانه است و در تاریخچه ذخیره نمی‌شود.
                </p>
              )}
            </div>
          </div>

          {!isNearBottom && (
            <button
              onClick={scrollToLatest}
              className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 h-9 px-4 rounded-full bg-neutral-900 border border-neutral-700 text-neutral-200 text-xs shadow-lg hover:bg-neutral-800 transition-colors animate-in fade-in slide-in-from-bottom-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
              aria-label="بازگشت به آخرین پیام"
              title="بازگشت به آخرین پیام"
            >
              <ArrowDown size={14} />
              بازگشت به آخرین پیام
            </button>
          )}
        </div>

        <ChatInputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}