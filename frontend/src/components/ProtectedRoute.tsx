import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ChatSessionsProvider } from '../context/ChatSessionsContext'
import { DocumentsProvider } from '../context/DocumentsContext'
import Sidebar from './Sidebar'

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <ChatSessionsProvider>
      <DocumentsProvider>
        <div className="flex">
          <Sidebar />
          <div className="flex-1 min-w-0">
            <Outlet />
          </div>
        </div>
      </DocumentsProvider>
    </ChatSessionsProvider>
  )
}
