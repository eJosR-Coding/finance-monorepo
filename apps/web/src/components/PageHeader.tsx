/** Page title + subtitle on the left, actions on the right. */

import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 24,
        flexWrap: 'wrap',
        marginBottom: 28,
      }}
    >
      <div>
        <h1 style={{ fontSize: 26, marginBottom: subtitle === undefined ? 0 : 6 }}>{title}</h1>
        {subtitle !== undefined && (
          <p style={{ fontSize: 14, opacity: 0.62, margin: 0 }}>{subtitle}</p>
        )}
      </div>
      {actions !== undefined && <div style={{ display: 'flex', gap: 10 }}>{actions}</div>}
    </div>
  )
}

export function Breadcrumb({ children }: { children: ReactNode }) {
  return (
    <div style={{ fontSize: 13, opacity: 0.6, marginBottom: 10 }}>{children}</div>
  )
}
