/** Loading, empty and error states. Every list screen leans on these. */

import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import type { IconName } from '@/components/Icon'

export function TableSkeleton({ rows = 4, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div aria-busy="true" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex', gap: 2 }}>
          {Array.from({ length: columns }).map((__, cellIndex) => (
            <div key={cellIndex} className="skeleton" style={{ height: 34, flex: 1 }} />
          ))}
        </div>
      ))}
    </div>
  )
}

export function CardsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div
      aria-busy="true"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${count}, minmax(180px, 1fr))`,
        gap: 16,
      }}
    >
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="skeleton" style={{ height: 86 }} />
      ))}
    </div>
  )
}

interface EmptyStateProps {
  icon?: IconName
  message: string
  action?: ReactNode
}

export function EmptyState({ icon = 'wallet', message, action }: EmptyStateProps) {
  return (
    <div
      style={{
        border: '1px solid var(--divider)',
        padding: 40,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
        textAlign: 'center',
      }}
    >
      <Icon name={icon} size={28} className="opacity-40" />
      <p style={{ margin: 0, fontSize: 14, opacity: 0.65 }}>{message}</p>
      {action}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useTranslation()
  return (
    <div
      role="alert"
      style={{
        border: '1px solid var(--color-accent)',
        background: 'var(--color-accent-100)',
        color: 'var(--color-accent-800)',
        padding: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        fontSize: 13.5,
      }}
    >
      <Icon name="alert-triangle" size={18} />
      <span style={{ flex: 1 }}>{message}</span>
      {onRetry !== undefined && (
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          {t('common.retry')}
        </button>
      )}
    </div>
  )
}

export function InlineError({ message }: { message: string }) {
  return (
    <p
      role="alert"
      style={{
        margin: '12px 0 0',
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--color-accent-700)',
      }}
    >
      {message}
    </p>
  )
}
