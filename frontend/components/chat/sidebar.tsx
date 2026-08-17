'use client'

import { useEffect, useState } from 'react'
import { Plus, Trash2, LogOut, MessageSquare } from 'lucide-react'
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
}: SidebarProps) {
  const [sessions, setSessions] = useState<SessionSummary[]>([])

  useEffect(() => {
    listSessions(user.user_id).then(setSessions).catch(() => setSessions([]))
  }, [user.user_id, refreshKey])

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    await deleteSession(user.user_id, sessionId)
    setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
    if (activeSessionId === sessionId) onNewConversation()
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
          transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0'}
          md:flex
        `}
        dir="rtl"
      >
      <div className="shrink-0 p-4 space-y-4">
        <div className="flex items-center gap-2.5 px-1">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] flex items-center justify-center shadow-[0_0_15px_-3px_rgba(224,138,79,0.6)]">
            <span className="font-en text-white font-bold text-xs">Rad</span>
          </div>
          <span className="font-en text-white font-semibold text-sm">Rad AI</span>
        </div>

        <button
          onClick={handleNewConversationMobile}
          className="w-full flex items-center justify-center gap-2 h-10 rounded-lg bg-[#B5723A] hover:bg-[#8B4A28] text-white text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          گفتگوی جدید
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto px-3 space-y-1">
        <p className="text-[11px] text-neutral-500 px-2 mb-2 font-medium">گفتگوها</p>
        {sessions.length === 0 && <p className="text-xs text-neutral-600 px-2">هنوز گفتگویی ثبت نشده</p>}
        {sessions.map((s) => (
          <button
            key={s.session_id}
            onClick={() => handleSelectMobile(s.session_id)}
            className={`group w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-sm text-right transition-colors ${
              activeSessionId === s.session_id
                ? 'bg-[#E08A4F]/12 text-white border border-[#E08A4F]/30'
                : 'text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200 border border-transparent'
            }`}
          >
            <MessageSquare size={14} className="shrink-0 opacity-60" />
            <span className="flex-1 truncate">{s.title}</span>
            <span
              onClick={(e) => handleDelete(e, s.session_id)}
              className="opacity-0 group-hover:opacity-100 text-neutral-500 hover:text-red-400 transition-opacity p-1"
            >
              <Trash2 size={13} />
            </span>
          </button>
        ))}
      </div>

      <div className="shrink-0 p-4 border-t border-neutral-800/80 space-y-3">
        <div className="px-1">
          <p className="text-sm text-neutral-200 font-medium">{user.username}</p>
          <p className="text-xs text-neutral-500">{roleLabels[user.role] || user.role}</p>
        </div>
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 h-9 rounded-lg border border-neutral-800 text-neutral-400 hover:text-white hover:border-neutral-700 text-sm transition-colors"
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