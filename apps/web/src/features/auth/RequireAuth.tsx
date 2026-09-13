/** Route guard: bounce to /login when there is no session. */

import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { ErrorState } from '@/components/States'
import { useAuth } from '@/features/auth/AuthContext'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading, sessionError, retrySession } = useAuth()
  const location = useLocation()
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', opacity: 0.6 }}>
        {t('common.loading')}
      </div>
    )
  }

  // The API was unreachable, so we genuinely don't know if the session is
  // valid. Bouncing to /login here would look like a random logout.
  if (user === null && sessionError !== null) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', padding: 24 }}>
        <div style={{ maxWidth: 520, width: '100%' }}>
          <ErrorState message={sessionError} onRetry={retrySession} />
        </div>
      </div>
    )
  }

  if (user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}
