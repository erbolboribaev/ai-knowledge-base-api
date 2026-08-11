import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { ChatSession } from '../types'

interface ChatSessionsContextValue {
  sessions: ChatSession[]
  newSession: () => string
  updateSession: (id: string, updater: (session: ChatSession) => ChatSession) => void
  getSession: (id: string | undefined) => ChatSession | undefined
}

const ChatSessionsContext = createContext<ChatSessionsContextValue | null>(null)
const STORAGE_KEY = 'chat_sessions'
const MAX_SESSIONS = 10

function makeSession(): ChatSession {
  return { id: crypto.randomUUID(), title: 'New chat', messages: [] }
}

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.slice(0, MAX_SESSIONS)
      }
    }
  } catch {
    // yaroqsiz ma'lumot bo'lsa, yangi suhbat bilan boshlaymiz
  }
  return [makeSession()]
}

export function ChatSessionsProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  }, [sessions])

  function newSession(): string {
    const session = makeSession()
    setSessions((prev) => [session, ...prev].slice(0, MAX_SESSIONS))
    return session.id
  }

  function updateSession(id: string, updater: (session: ChatSession) => ChatSession) {
    setSessions((prev) => prev.map((s) => (s.id === id ? updater(s) : s)))
  }

  function getSession(id: string | undefined): ChatSession | undefined {
    return sessions.find((s) => s.id === id)
  }

  return (
    <ChatSessionsContext.Provider value={{ sessions, newSession, updateSession, getSession }}>
      {children}
    </ChatSessionsContext.Provider>
  )
}

export function useChatSessions(): ChatSessionsContextValue {
  const context = useContext(ChatSessionsContext)
  if (!context) {
    throw new Error('useChatSessions must be used within a ChatSessionsProvider')
  }
  return context
}
