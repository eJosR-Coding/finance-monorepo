/** Label + control + hint/error. Keeps every form row consistent. */

import type { ReactNode } from 'react'

import { Tooltip } from '@/components/Tooltip'

interface FieldProps {
  label: string
  htmlFor?: string
  tip?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
}

export function Field({ label, htmlFor, tip, hint, error, children, className }: FieldProps) {
  return (
    <div className={`field ${className ?? ''}`}>
      <label htmlFor={htmlFor}>
        {label}
        {tip !== undefined && <Tooltip text={tip} />}
      </label>
      {children}
      {error !== undefined ? (
        <p className="field-error">{error}</p>
      ) : (
        hint !== undefined && <p className="field-hint">{hint}</p>
      )}
    </div>
  )
}
