/** Bottom-right toasts. One at a time, auto-dismissed - nothing fancier needed. */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { Icon } from '@/components/Icon'

type ToastTone = 'success' | 'error'

interface Toast {
  id: number
  message: string
  tone: ToastTone
}

interface ToastValue {
  notify: (message: string, tone?: ToastTone) => void
}

const ToastContext = createContext<ToastValue | null>(null)
const DISMISS_AFTER_MS = 3200

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null)

  const notify = useCallback((message: string, tone: ToastTone = 'success') => {
    setToast({ id: Date.now(), message, tone })
  }, [])

  useEffect(() => {
    if (toast === null) return
    const timer = window.setTimeout(() => setToast(null), DISMISS_AFTER_MS)
    return () => window.clearTimeout(timer)
  }, [toast])

  const value = useMemo<ToastValue>(() => ({ notify }), [notify])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast !== null && (
        <div
          className={toast.tone === 'error' ? 'toast toast-error' : 'toast'}
          role="status"
          aria-live="polite"
        >
          <Icon name={toast.tone === 'error' ? 'alert-triangle' : 'check-circle'} size={16} />
          {toast.message}
        </div>
      )}
    </ToastContext.Provider>
  )
}

export function useToast(): ToastValue {
  const value = useContext(ToastContext)
  if (value === null) throw new Error('useToast must be used inside <ToastProvider>')
  return value
}
