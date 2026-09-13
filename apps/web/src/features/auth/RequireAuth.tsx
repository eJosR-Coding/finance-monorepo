/** Route guard: bounce to /login when there is no session. */

import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useAuth } from '@/features/auth/AuthContext'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', opacity: 0.6 }}>
        {t('common.loading')}
      </div>
    )
  }

  if (user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}
