import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function OAuthCallback() {
  const [searchParams] = useSearchParams()
  const { setTokens } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const accessToken = searchParams.get('access_token')
    const refreshToken = searchParams.get('refresh_token')

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken)
      navigate('/chat/new', { replace: true })
    } else {
      navigate('/login', { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex items-center gap-2 text-stone text-sm">
        <Loader2 size={18} className="animate-spin" />
        Signing you in...
      </div>
    </div>
  )
}
