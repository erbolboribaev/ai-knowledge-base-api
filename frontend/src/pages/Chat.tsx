import { useState, useRef, useEffect, type FormEvent, type ChangeEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, Sparkles, FileSearch, Globe, Plus, FileUp, Image, X } from 'lucide-react'
import client from '../api/client'
import { useChatSessions } from '../context/ChatSessionsContext'
import { useDocuments } from '../context/DocumentsContext'
import type { ChatAskResponse } from '../types'

export default function Chat() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { sessions, getSession, updateSession, newSession } = useChatSessions()
  const { uploadDocument, uploadImageDocument } = useDocuments()

  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [webSearchOn, setWebSearchOn] = useState(false)
  const [uploadingFile, setUploadingFile] = useState(false)

  const endRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)

  const session = getSession(sessionId)

  useEffect(() => {
    if (!session) {
      if (sessions.length > 0) {
        navigate(`/chat/${sessions[0].id}`, { replace: true })
      } else {
        const id = newSession()
        navigate(`/chat/${id}`, { replace: true })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, sessions.length])

  const messages = session?.messages ?? []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  async function handleAsk(e: FormEvent) {
    e.preventDefault()
    if (!question.trim() || !session) return

    const userText = question
    const isFirstMessage = messages.length === 0

    updateSession(session.id, (s) => ({
      ...s,
      title: isFirstMessage ? userText.slice(0, 40) : s.title,
      messages: [...s.messages, { role: 'user', text: userText }],
    }))
    setQuestion('')
    setLoading(true)

    try {
      const { data } = await client.post<ChatAskResponse>('/chat/ask', {
        question: userText,
        use_web_search: webSearchOn,
      })
      updateSession(session.id, (s) => ({
        ...s,
        messages: [
          ...s.messages,
          { role: 'assistant', text: data.answer, sources: data.sources, webSources: data.web_sources },
        ],
      }))
    } catch {
      updateSession(session.id, (s) => ({
        ...s,
        messages: [
          ...s.messages,
          { role: 'assistant', text: 'Something went wrong. Please try again.', sources: [], webSources: [] },
        ],
      }))
    } finally {
      setLoading(false)
    }
  }

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setMenuOpen(false)
    setUploadingFile(true)
    try {
      const text = await file.text()
      await uploadDocument(file.name, text)
    } finally {
      setUploadingFile(false)
      e.target.value = ''
    }
  }

  async function handleImageChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setMenuOpen(false)
    setUploadingFile(true)
    try {
      await uploadImageDocument(file)
    } finally {
      setUploadingFile(false)
      e.target.value = ''
    }
  }

  function handleWebSearchToggle() {
    setWebSearchOn(!webSearchOn)
    setMenuOpen(false)
  }

  if (!session) return null

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 flex flex-col min-h-screen">
      <h1 className="font-serif text-xl font-semibold text-ink mb-6 truncate">
        {session.title}
      </h1>

      <div className="flex-1 space-y-5 mb-6">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <Sparkles size={28} className="mx-auto text-amber/50 mb-3" />
            <p className="text-stone text-sm">
              Ask a question, or use the + button to add files, screenshots, or search the web.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div className="flex justify-end">
                <p className="bg-ink text-paper px-4 py-2.5 rounded-sm max-w-lg text-sm shadow-sm">
                  {msg.text}
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-w-xl">
                <p className="text-ink text-sm leading-relaxed">{msg.text}</p>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="space-y-1.5 mt-2">
                    {msg.sources.map((src, j) => (
                      <div key={j} className="border-l-2 border-amber bg-amber/5 pl-3 py-1.5 rounded-r-sm">
                        <p className="font-mono text-[11px] text-stone mb-0.5 flex items-center gap-1.5">
                          <FileSearch size={11} />
                          {src.document_filename} · {(src.similarity_score * 100).toFixed(0)}% match
                        </p>
                        <p className="text-xs text-stone italic">"{src.content}"</p>
                      </div>
                    ))}
                  </div>
                )}

                {msg.webSources && msg.webSources.length > 0 && (
                  <div className="space-y-1.5 mt-2">
                    {msg.webSources.map((src, j) => (
                      <a key={j}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block border-l-2 border-ink/30 bg-ink/5 pl-3 py-1.5 rounded-r-sm hover:bg-ink/10 transition"
                      >
                        <p className="font-mono text-[11px] text-ink/70 mb-0.5 flex items-center gap-1.5">
                          <Globe size={11} />
                          {src.title}
                        </p>
                        <p className="text-xs text-stone truncate">{src.url}</p>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-stone text-sm">
            <span className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-stone/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-stone/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-stone/50 rounded-full animate-bounce" />
            </span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {webSearchOn && (
        <div className="mb-2 flex items-center gap-1.5 w-fit">
          <span className="flex items-center gap-1.5 bg-ink/5 text-ink text-xs px-2.5 py-1 rounded-full">
            <Globe size={12} />
            Web search on
            <button
              onClick={() => setWebSearchOn(false)}
              aria-label="Turn off web search"
              className="hover:text-error transition"
            >
              <X size={12} />
            </button>
          </span>
        </div>
      )}
      {uploadingFile && (
        <p className="mb-2 text-xs text-stone italic">Uploading...</p>
      )}

      <form onSubmit={handleAsk} className="flex gap-2 sticky bottom-6 relative">
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Add files, screenshots, or web search"
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            className="h-full px-3 border border-stone/25 bg-white rounded-sm hover:border-amber hover:text-amber transition flex items-center justify-center"
          >
            <Plus size={18} />
          </button>

          {menuOpen && (
            <div className="absolute bottom-full left-0 mb-2 bg-white border border-stone/15 rounded-sm shadow-md overflow-hidden w-52">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-ink hover:bg-ink/5 transition text-left"
              >
                <FileUp size={16} className="text-stone" />
                Add files or photos
              </button>
              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-ink hover:bg-ink/5 transition text-left"
              >
                <Image size={16} className="text-stone" />
                Add screenshots
              </button>
              <button
                type="button"
                onClick={handleWebSearchToggle}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-ink hover:bg-ink/5 transition text-left"
              >
                <Globe size={16} className={webSearchOn ? 'text-amber' : 'text-stone'} />
                Web search
                {webSearchOn && <span className="ml-auto text-amber text-xs">On</span>}
              </button>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,text/plain"
            className="hidden"
            onChange={handleFileChange}
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={handleImageChange}
          />
        </div>

        <input
          id="chat-question"
          name="question"
          type="text"
          autoComplete="off"
          aria-label="Ask a question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 px-4 py-2.5 border border-stone/25 bg-white rounded-sm text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-amber/30 focus:border-amber transition"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-ink text-paper px-5 py-2.5 rounded-sm text-sm font-medium hover:bg-ink/90 transition disabled:opacity-50 flex items-center gap-2"
        >
          <Send size={15} />
          Ask
        </button>
      </form>
    </div>
  )
}
