import { Link } from 'react-router-dom'
import { FileText, Search, MessageSquare, ArrowRight, type LucideIcon } from 'lucide-react'

interface Feature {
  icon: LucideIcon
  title: string
  text: string
}

const FEATURES: Feature[] = [
  {
    icon: FileText,
    title: 'Upload documents',
    text: 'Add any text-based document to your personal knowledge base in seconds.',
  },
  {
    icon: Search,
    title: 'Semantic search',
    text: 'Your documents are automatically chunked and embedded for meaning-based retrieval.',
  },
  {
    icon: MessageSquare,
    title: 'Ask questions',
    text: 'Get precise answers grounded in your own documents, with sources cited.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen">
      <nav className="max-w-5xl mx-auto px-4 py-5 flex items-center justify-between">
        <div className="border-l-2 border-amber pl-3">
          <p className="font-mono text-[10px] text-stone uppercase tracking-wider">
            Knowledge Base
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm text-ink hover:text-amber transition">
            Sign in
          </Link>
          <Link
            to="/register"
            className="text-sm bg-ink text-paper px-4 py-2 rounded-sm hover:bg-ink/90 transition"
          >
            Get started
          </Link>
        </div>
      </nav>

      <header className="max-w-3xl mx-auto px-4 pt-20 pb-16 text-center">
        <p className="font-mono text-xs text-amber uppercase tracking-wider mb-4">
          Retrieval-Augmented Generation
        </p>
        <h1 className="font-serif text-5xl font-semibold text-ink leading-tight mb-6">
          Ask questions about your own documents
        </h1>
        <p className="text-stone text-lg mb-8 max-w-xl mx-auto">
          Upload anything — policies, notes, research — and get precise, cited answers
          drawn only from what you've shared.
        </p>
        <Link
          to="/register"
          className="inline-flex items-center gap-2 bg-ink text-paper px-6 py-3 rounded-sm font-medium hover:bg-ink/90 transition"
        >
          Create your knowledge base
          <ArrowRight size={18} />
        </Link>
      </header>

      <section className="max-w-5xl mx-auto px-4 pb-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div
              key={title}
              className="bg-white border border-stone/15 rounded-sm p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-sm bg-amber/10 flex items-center justify-center mb-4">
                <Icon size={20} className="text-amber" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-ink mb-2">{title}</h3>
              <p className="text-sm text-stone leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
