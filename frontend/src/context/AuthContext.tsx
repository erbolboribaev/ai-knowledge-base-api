import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import client from '../api/client'
import type { User } from '../types'

interface AuthContextValue {
  isAuthenticated: boolean
  user: User | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  setTokens: (accessToken: string, refreshToken: string) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('access_token')
  )
  const [user, setUser] = useState<User | null>(null)

  async function fetchUser() {
    try {
      const { data } = await client.get<User>('/auth/me')
      setUser(data)
    } catch {
      setUser(null)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchUser()
    }
  }, [isAuthenticated])

  async function login(email: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const { data } = await client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    setIsAuthenticated(true)
  }

  async function register(email: string, password: string) {
    await client.post('/auth/register', { email, password })
  }

  function setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    setIsAuthenticated(true)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, register, logout, setTokens }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
