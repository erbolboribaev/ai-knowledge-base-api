import { useEffect, useState } from 'react'
import { X, FileText, Trash2, Loader2 } from 'lucide-react'
import client from '../api/client'
import { useDocuments } from '../context/DocumentsContext'
import type { DocumentDetail } from '../types'

interface DocumentModalProps {
  documentId: string
  onClose: () => void
}

export default function DocumentModal({ documentId, onClose }: DocumentModalProps) {
  const [doc, setDoc] = useState<DocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const { deleteDocument } = useDocuments()

  useEffect(() => {
    let active = true
    setLoading(true)
    client.get<DocumentDetail>(`/documents/${documentId}`).then(({ data }) => {
      if (active) {
        setDoc(data)
        setLoading(false)
      }
    })
    return () => {
      active = false
    }
  }, [documentId])

  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  async function handleDelete() {
    await deleteDocument(documentId)
    onClose()
  }

  return (
    <div
      className="fixed inset-0 bg-ink/30 flex items-center justify-center z-50 px-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="bg-white rounded-sm shadow-lg max-w-lg w-full max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Document content"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone/15">
          <div className="flex items-center gap-2 min-w-0">
            <FileText size={16} className="text-ink/60 flex-shrink-0" />
            <p className="font-medium text-ink text-sm truncate">
              {doc?.filename ?? 'Loading...'}
            </p>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={handleDelete}
              className="text-stone hover:text-error transition p-1.5 rounded-sm hover:bg-error/5"
              aria-label="Delete document"
            >
              <Trash2 size={15} />
            </button>
            <button
              onClick={onClose}
              className="text-stone hover:text-ink transition p-1.5 rounded-sm hover:bg-ink/5"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="px-5 py-4 overflow-y-auto">
          {loading || !doc ? (
            <div className="flex items-center gap-2 text-stone text-sm py-6 justify-center">
              <Loader2 size={16} className="animate-spin" />
              Loading...
            </div>
          ) : (
            <p className="text-sm text-ink/80 whitespace-pre-wrap leading-relaxed">
              {doc.content}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
