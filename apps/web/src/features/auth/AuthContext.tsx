/** Session state: who is logged in, plus login/logout. */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { authApi } from '@/services/api'
import { ApiError, getToken, setToken } from '@/services/http'
import type { User } from '@/types/api'

interface AuthValue {
  user: User | null
  isLoading: boolean
  /** Set when the session could not be checked because the API was unreachable. */
  sessionError: string | null
  retrySession: () => void
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    // A token in localStorage is only a hint; the API decides if it's still good.
    if (getToken() === null) {
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    setSessionError(null)
    authApi
      .me()
      .then((current) => {
        setUser(current)
        setSessionError(null)
      })
      .catch((error: unknown) => {
        const unreachable = error instanceof ApiError && error.code === 'NETWORK_ERROR'
        if (unreachable) {
          // Don't torch a valid session over a network blip: keep the token so a
          // retry works once the API is back, and say what actually happened.
          setSessionError(error.message)
          return
        }
        setToken(null)
      })
      .finally(() => setIsLoading(false))
  }, [attempt])

  const retrySession = useCallback(() => setAttempt((value) => value + 1), [])

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password)
    setToken(response.access_token)
    setUser(response.user)
    setSessionError(null)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    setSessionError(null)
  }, [])

  const value = useMemo<AuthValue>(
    () => ({ user, isLoading, sessionError, retrySession, login, logout }),
    [user, isLoading, sessionError, retrySession, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (value === null) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
