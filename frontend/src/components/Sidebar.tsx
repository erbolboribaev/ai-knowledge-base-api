import { useState, memo, type ComponentType } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Plus, LogOut, Library, CheckCircle2, Clock, XCircle, Loader2,
  ChevronDown, ChevronRight, PanelLeftClose, PanelLeftOpen,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useChatSessions } from '../context/ChatSessionsContext'
import { useDocuments } from '../context/DocumentsContext'
import DocumentModal from './DocumentModal'
import type { DocumentStatus } from '../types'

const STATUS_ICON: Record<DocumentStatus, ComponentType<{ size?: number; className?: string }>> = {
  pending: Clock,
  processing: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
}

const STATUS_COLOR: Record<DocumentStatus, string> = {
  pending: 'text-stone',
  processing: 'text-amber',
  completed: 'text-success',
  failed: 'text-error',
}

function isMobileViewport(): boolean {
  return typeof window !== 'undefined' && window.innerWidth < 768
}

function Sidebar() {
  const { user, logout } = useAuth()
  const { sessions, newSession } = useChatSessions()
  const { documents } = useDocuments()
  const navigate = useNavigate()
  const { sessionId: activeSessionId } = useParams<{ sessionId: string }>()

  // Mobil ekranlarda sidebar standart holatda yig'ilgan boshlanadi,
  // shunda birinchi yuklanishda butun ekranni to'sib qo'ymaydi.
  const [collapsed, setCollapsed] = useState(isMobileViewport)
  const [chatsOpen, setChatsOpen] = useState(true)
  const [filesOpen, setFilesOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [modalDocId, setModalDocId] = useState<string | null>(null)

  function handleNewChat() {
    const id = newSession()
    navigate(`/chat/${id}`)
    if (isMobileViewport()) setCollapsed(true)
  }

  function handleSelectSession(id: string) {
    navigate(`/chat/${id}`)
    if (isMobileViewport()) setCollapsed(true)
  }

  if (collapsed) {
    return (
      <div className="w-12 flex-shrink-0 border-r border-stone/15 bg-white flex flex-col items-center py-4 h-screen sticky top-0 z-30">
        <button
          onClick={() => setCollapsed(false)}
          title="Open sidebar"
          aria-label="Open sidebar"
          className="p-2 rounded-sm text-stone hover:bg-ink/5 hover:text-ink transition"
        >
          <PanelLeftOpen size={18} />
        </button>
      </div>
    )
  }

  return (
    <>
      {/* Mobil ekranda ochiq sidebar orqasida qorong'i fon - bosilsa yopiladi */}
      <div
        className="fixed inset-0 bg-ink/30 z-30 md:hidden"
        onClick={() => setCollapsed(true)}
      />

      <aside className="fixed md:sticky inset-y-0 md:inset-auto left-0 top-0 z-40 md:z-auto w-64 flex-shrink-0 border-r border-stone/15 bg-white flex flex-col h-screen">
        <div className="p-4 flex items-center justify-between border-b border-stone/15">
          <div className="flex items-center gap-2 min-w-0">
            <Library size={18} className="text-amber flex-shrink-0" />
            <span className="text-sm font-medium text-ink truncate">Knowledge Base</span>
          </div>
          <button
            onClick={() => setCollapsed(true)}
            title="Close sidebar"
            aria-label="Close sidebar"
            className="p-1.5 rounded-sm text-stone hover:bg-ink/5 hover:text-ink transition flex-shrink-0"
          >
            <PanelLeftClose size={17} />
          </button>
        </div>

        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 text-sm bg-ink text-paper rounded-sm py-2 hover:bg-ink/90 transition"
          >
            <Plus size={15} />
            New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
          <div>
            <button
              onClick={() => setChatsOpen(!chatsOpen)}
              className="w-full flex items-center gap-1 px-2 py-1.5 text-[11px] text-stone uppercase tracking-wider hover:text-ink transition"
            >
              {chatsOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Recent chats
            </button>
            {chatsOpen && (
              <div className="space-y-0.5 mt-0.5">
                {sessions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelectSession(s.id)}
                    className={`w-full text-left px-2.5 py-1.5 rounded-sm text-xs truncate transition ${
                      activeSessionId === s.id ? 'bg-ink/5 text-ink' : 'text-stone hover:bg-ink/5'
                    }`}
                  >
                    {s.title}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <button
              onClick={() => setFilesOpen(!filesOpen)}
              className="w-full flex items-center gap-1 px-2 py-1.5 text-[11px] text-stone uppercase tracking-wider hover:text-ink transition"
            >
              {filesOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Files
            </button>
            {filesOpen && (
              <div className="space-y-0.5 mt-0.5">
                {documents.length === 0 && (
                  <p className="px-2.5 py-1.5 text-xs text-stone/60">No files yet</p>
                )}
                {documents.map((doc) => {
                  const StatusIcon = STATUS_ICON[doc.status]
                  return (
                    <button
                      key={doc.id}
                      onClick={() => setModalDocId(doc.id)}
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-sm text-xs text-stone hover:bg-ink/5 transition text-left"
                      title={doc.filename}
                    >
                      <StatusIcon
                        size={12}
                        className={`flex-shrink-0 ${STATUS_COLOR[doc.status]} ${doc.status === 'processing' ? 'animate-spin' : ''}`}
                      />
                      <span className="truncate">{doc.filename}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        <div className="relative border-t border-stone/15 p-3">
          {accountOpen && (
            <div className="absolute bottom-full left-3 right-3 mb-1 bg-white border border-stone/15 rounded-sm shadow-md overflow-hidden">
              <button
                onClick={logout}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-stone hover:bg-error/5 hover:text-error transition"
              >
                <LogOut size={15} />
                Sign out
              </button>
            </div>
          )}
          <button
            onClick={() => setAccountOpen(!accountOpen)}
            className="w-full flex items-center gap-2.5 px-2 py-1.5 rounded-sm hover:bg-ink/5 transition"
          >
            <div className="w-7 h-7 rounded-full bg-amber/15 text-amber flex items-center justify-center text-xs font-medium flex-shrink-0">
              {user?.email?.[0]?.toUpperCase() ?? '?'}
            </div>
            <span className="text-xs text-ink truncate">{user?.email ?? 'Loading...'}</span>
          </button>
        </div>

        {modalDocId && (
          <DocumentModal documentId={modalDocId} onClose={() => setModalDocId(null)} />
        )}
      </aside>
    </>
  )
}


export default memo(Sidebar)
