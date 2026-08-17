'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
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

export default function ChatPage() {
  const router = useRouter()
  const [user, setUser] = useState<StoredUser | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showTechnical, setShowTechnical] = useState(false)
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0)
  const [confidentialNotice, setConfidentialNotice] = useState(false)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const raw = localStorage.getItem('rad_ai_user')
    if (!raw) {
      router.push('/')
      return
    }
    setUser(JSON.parse(raw))
  }, [router])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  const handleNewConversation = useCallback(() => {
    setSessionId(null)
    setMessages([])
    setConfidentialNotice(false)
  }, [])

  const handleSelectSession = useCallback(
    async (id: string) => {
      if (!user) return
      const msgs = await loadMessages(user.user_id, id)
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
    <div className="h-screen w-full flex overflow-hidden">
      <Sidebar
        user={user}
        activeSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        refreshKey={sidebarRefreshKey}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <ChatHeader
          showTechnical={showTechnical}
          onToggleTechnical={setShowTechnical}
          onOpenSidebar={() => setIsMobileSidebarOpen(true)}
        />

        <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 md:px-8 py-6">
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

        <ChatInputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}