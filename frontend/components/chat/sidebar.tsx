'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { Plus, Trash2, LogOut, MessageSquare, PanelLeftClose } from 'lucide-react'
import { listSessions, deleteSession } from '@/lib/api'
import { StoredUser, SessionSummary } from '@/lib/types'

const roleLabels: Record<string, string> = {
  staff: 'کارمند',
  supervisor: 'سرپرست',
  manager: 'مدیر',
}

type SidebarProps = {
  user: StoredUser
  activeSessionId: string | null
  onSelectSession: (sessionId: string) => void
  onNewConversation: () => void
  onLogout: () => void
  refreshKey: number
  isMobileOpen: boolean
  onMobileClose: () => void
  collapsed?: boolean
  onToggleSidebar?: () => void
}

export function Sidebar({
  user,
  activeSessionId,
  onSelectSession,
  onNewConversation,
  onLogout,
  refreshKey,
  isMobileOpen,
  onMobileClose,
  collapsed = false,
  onToggleSidebar,
}: SidebarProps) {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    listSessions()
      .then((data) => {
        setSessions(data)
        setLoadError(null)
      })
      .catch((err) => {
        setSessions([])
        setLoadError(err instanceof Error ? err.message : "خطا در دریافت گفتگوها")
      })
  }, [refreshKey])

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    try {
      await deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
      if (activeSessionId === sessionId) onNewConversation()
    } catch {
      // 401/403/404 already surfaced through the shared api error handler.
    }
  }

  const handleSelectMobile = (id: string) => {
    onSelectSession(id)
    onMobileClose()
  }

  const handleNewConversationMobile = () => {
    onNewConversation()
    onMobileClose()
  }

  return (
    <>
      {/* Mobile overlay backdrop — only rendered/visible when the drawer is open */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed md:static top-0 bottom-0 right-0 z-50
          h-screen md:h-full
          w-72 shrink-0 flex flex-col border-l border-neutral-800/80 bg-neutral-950 md:bg-neutral-950/60 backdrop-blur-sm
          transition-[transform,width,opacity] duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}
          ${collapsed ? 'md:w-0 md:overflow-hidden md:border-l-0 md:opacity-0 md:pointer-events-none' : 'md:w-72'}
          md:flex
        `}
        dir="rtl"
      >
      <div className="shrink-0 p-4 space-y-4">
                <div className="flex items-center gap-2.5 px-1">
          <Image src="/logo.png" alt="Rad AI" width={36} height={36} className="w-9 h-9 object-contain shrink-0" />
          <span className="font-en text-white font-semibold text-sm">Rad AI</span>
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="hidden md:flex ms-auto w-8 h-8 items-center justify-center rounded-lg text-neutral-500 hover:text-white hover:bg-neutral-900 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
              aria-label="بستن نوار کناری"
              title="بستن نوار کناری"
            >
              <PanelLeftClose size={17} />
            </button>
          )}
        </div>

        <button
          onClick={handleNewConversationMobile}
          className="w-full flex items-center justify-center gap-2 h-10 rounded-lg bg-[#B5723A] hover:bg-[#8B4A28] text-white text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
        >
          <Plus size={16} />
          گفتگوی جدید
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto px-3 space-y-1">
        <p className="text-[11px] text-neutral-500 px-2 mb-2 font-medium">گفتگوها</p>
        {loadError && <p className="text-xs text-red-400 px-2 mb-2">{loadError}</p>}
        {sessions.length === 0 && !loadError && <p className="text-xs text-neutral-600 px-2">هنوز گفتگویی ثبت نشده</p>}
        {sessions.map((s) => (
          <div
            key={s.session_id}
            className={`group w-full flex items-center rounded-lg border text-sm transition-colors ${
              activeSessionId === s.session_id
                ? 'bg-[#E08A4F]/12 border-[#E08A4F]/30'
                : 'border-transparent hover:bg-neutral-900'
            }`}
          >
            <button
              onClick={() => handleSelectMobile(s.session_id)}
              className={`flex-1 min-w-0 flex items-center gap-2 px-2.5 py-2 text-right rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60 ${
                activeSessionId === s.session_id ? 'text-white' : 'text-neutral-400 group-hover:text-neutral-200'
              }`}
            >
              <MessageSquare size={14} className="shrink-0 opacity-60" />
              <span className="flex-1 truncate">{s.title}</span>
            </button>
            <button
              onClick={(e) => handleDelete(e, s.session_id)}
              aria-label="حذف گفتگو"
              title="حذف گفتگو"
              className="shrink-0 mr-0.5 p-1.5 rounded-md text-neutral-500 hover:text-red-400 transition-opacity opacity-0 group-hover:opacity-100 focus-visible:opacity-100 max-sm:opacity-100 cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <div className="shrink-0 p-4 border-t border-neutral-800/80 space-y-3">
        <div className="px-1">
          <p className="text-sm text-neutral-200 font-medium">{user.username}</p>
          <p className="text-xs text-neutral-500">{roleLabels[user.role] || user.role}</p>
        </div>
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 h-9 rounded-lg border border-neutral-800 text-neutral-400 hover:text-white hover:border-neutral-700 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E08A4F]/60"
        >
          <LogOut size={14} />
          خروج
        </button>
        <p className="font-en text-[10px] text-neutral-700 text-center pt-1">Rad AI v0.1 · Prototype</p>
      </div>
    </aside>
    </>
  )
}