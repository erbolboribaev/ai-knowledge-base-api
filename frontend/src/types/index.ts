export interface User {
  id: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface DocumentSummary {
  id: string
  filename: string
  status: DocumentStatus
  created_at: string
}

export interface DocumentDetail extends DocumentSummary {
  content: string
}

export interface SourceChunk {
  document_filename: string
  content: string
  similarity_score: number
}

export interface WebSource {
  title: string
  url: string
  snippet: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  sources?: SourceChunk[]
  webSources?: WebSource[]
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
}

export interface ChatAskResponse {
  answer: string
  sources: SourceChunk[]
  web_sources: WebSource[]
}
