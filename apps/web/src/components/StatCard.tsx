/** KPI card: kicker, big number, optional footnote. */

import type { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: ReactNode
  meta?: ReactNode
  tone?: 'default' | 'alert'
  size?: 'md' | 'sm'
}

export function StatCard({ label, value, meta, tone = 'default', size = 'md' }: StatCardProps) {
  return (
    <div className="card">
      <div className="card-kicker">{label}</div>
      <div
        className="card-value"
        style={{
          fontSize: size === 'sm' ? 19 : 24,
          color: tone === 'alert' ? 'var(--color-accent-700)' : undefined,
        }}
      >
        {value}
      </div>
      {meta !== undefined && <div className="card-meta">{meta}</div>}
    </div>
  )
}
