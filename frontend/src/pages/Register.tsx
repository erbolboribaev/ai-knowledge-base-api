import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Library, Mail, Lock, UserPlus, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { AxiosError } from 'axios'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register, login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(email, password)
      await login(email, password)
      navigate('/chat/new')
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>
      const detail = axiosErr.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Could not create account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white border border-stone/15 rounded-sm shadow-sm p-8">
        <div className="flex items-center gap-2 mb-1">
          <Library size={18} className="text-amber" />
          <p className="font-mono text-xs text-stone uppercase tracking-wider">
            Knowledge Base
          </p>
        </div>
        <h1 className="font-serif text-2xl font-semibold text-ink mb-6">
          Create account
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-stone mb-1.5">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone/50" />
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 border border-stone/25 bg-white rounded-sm text-sm focus:outline-none focus:ring-2 focus:ring-amber/30 focus:border-amber transition"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm text-stone mb-1.5">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone/50" />
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 border border-stone/25 bg-white rounded-sm text-sm focus:outline-none focus:ring-2 focus:ring-amber/30 focus:border-amber transition"
                placeholder="At least 8 characters"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-error border-l-2 border-error pl-3 py-1">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-ink text-paper py-2.5 rounded-sm font-medium hover:bg-ink/90 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Creating account...
              </>
            ) : (
              <>
                <UserPlus size={16} />
                Create account
              </>
            )}
          </button>
        </form>

        <div className="my-5 flex items-center gap-3">
          <div className="flex-1 h-px bg-stone/15" />
          <span className="text-xs text-stone">or</span>
          <div className="flex-1 h-px bg-stone/15" />
        </div>

        <button
          type="button"
          onClick={() => { window.location.href = '/api/v1/auth/github/login' }}
          className="w-full flex items-center justify-center gap-2 border border-stone/25 text-ink py-2.5 rounded-sm font-medium hover:bg-ink/5 transition"
        >
          Continue with GitHub
        </button>

        <p className="mt-6 text-sm text-stone text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-amber hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
