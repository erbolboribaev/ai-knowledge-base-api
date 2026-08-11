import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

// Har bir sahifa alohida "bo'lak" (chunk) sifatida yuklanadi - foydalanuvchi
// faqat o'zi ochgan sahifa uchun kerakli kodni yuklab oladi, boshlang'ich
// yuklama hajmi sezilarli kamayadi.
const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Chat = lazy(() => import('./pages/Chat'))
const OAuthCallback = lazy(() => import('./pages/OAuthCallback'))

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 size={24} className="animate-spin text-stone/50" />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/oauth/callback" element={<OAuthCallback />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/chat" element={<Navigate to="/chat/new" replace />} />
              <Route path="/chat/:sessionId" element={<Chat />} />
              <Route path="/documents" element={<Navigate to="/chat/new" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  )
}
