import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import client from '../api/client'
import type { DocumentSummary } from '../types'

interface DocumentsContextValue {
  documents: DocumentSummary[]
  refresh: () => Promise<void>
  uploadDocument: (filename: string, content: string) => Promise<void>
  uploadImageDocument: (file: File) => Promise<void>
  deleteDocument: (id: string) => Promise<void>
}

const DocumentsContext = createContext<DocumentsContextValue | null>(null)

export function DocumentsProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([])

  async function refresh() {
    const { data } = await client.get<DocumentSummary[]>('/documents/')
    setDocuments(data)
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 3000)
    return () => clearInterval(interval)
  }, [])

  async function uploadDocument(filename: string, content: string) {
    await client.post('/documents/', { filename, content })
    await refresh()
  }

  async function uploadImageDocument(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    await client.post('/documents/from-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await refresh()
  }

  async function deleteDocument(id: string) {
    await client.delete(`/documents/${id}`)
    await refresh()
  }

  return (
    <DocumentsContext.Provider
      value={{ documents, refresh, uploadDocument, uploadImageDocument, deleteDocument }}
    >
      {children}
    </DocumentsContext.Provider>
  )
}

export function useDocuments(): DocumentsContextValue {
  const context = useContext(DocumentsContext)
  if (!context) {
    throw new Error('useDocuments must be used within a DocumentsProvider')
  }
  return context
}
