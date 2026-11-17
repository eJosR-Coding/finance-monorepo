/** Split-screen sign in. No sidebar here. */

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Field } from '@/components/Field'
import { Icon } from '@/components/Icon'
import { InlineError } from '@/components/States'
import { useAuth } from '@/features/auth/AuthContext'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney, todayIso } from '@/lib/format'

export function LoginPage() {
  const { t } = useTranslation()
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('admin@prestameami.pe')
  const [password, setPassword] = useState('admin123')
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [forgotOpen, setForgotOpen] = useState(false)

  if (user !== null) return <Navigate to="/dashboard" replace />

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (caught) {
      setError(translateError(caught, t))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        minHeight: '100vh',
        background: 'var(--color-bg)',
      }}
    >
      <div
        style={{
          flex: '1 1 420px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '56px clamp(24px, 6vw, 88px)',
        }}
      >
        <div style={{ maxWidth: 380, width: '100%', margin: '0 auto' }}>
          <div
            style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 48 }}
          >
            <span
              style={{ width: 24, height: 24, background: 'var(--color-accent)', flex: 'none' }}
            />
            <span
              style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 19 }}
            >
              {t('common.appName')}
              <span style={{ color: 'var(--color-accent-700)' }}>{t('common.appSuffix')}</span>
            </span>
          </div>

          <h1 style={{ fontSize: 28, marginBottom: 8 }}>{t('auth.title')}</h1>
          <p style={{ fontSize: 14, opacity: 0.65, margin: '0 0 32px' }}>{t('auth.subtitle')}</p>

          <form
            onSubmit={onSubmit}
            style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
            noValidate
          >
            <Field label={t('auth.email')} htmlFor="email">
              <input
                id="email"
                className="input"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </Field>

            <Field label={t('auth.password')} htmlFor="password">
              <input
                id="password"
                className="input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </Field>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: -4,
                fontSize: 13,
              }}
            >
              <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(event) => setRemember(event.target.checked)}
                  style={{ accentColor: 'var(--color-accent)' }}
                />
                {t('auth.remember')}
              </label>
              <button
                type="button"
                className="muted"
                onClick={() => setForgotOpen(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  font: 'inherit',
                  textDecoration: 'underline',
                }}
              >
                {t('auth.forgot')}
              </button>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={busy}
              style={{ marginTop: 8 }}
            >
              {busy ? t('auth.submitting') : t('auth.submit')}
            </button>

            {error !== null && <InlineError message={error} />}
          </form>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginTop: 32,
              paddingTop: 20,
              borderTop: '1px solid var(--divider)',
              opacity: 0.55,
              fontSize: 12.5,
            }}
          >
            <Icon name="shield-check" size={15} />
            {t('auth.footer')}
          </div>
        </div>
      </div>

      <div
        style={{
          flex: '1 1 480px',
          background: 'var(--color-neutral-900)',
          color: 'var(--color-neutral-100)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '56px clamp(24px, 6vw, 80px)',
          minHeight: 340,
        }}
      >
        <div style={{ maxWidth: 420, width: '100%', margin: '0 auto' }}>
          <div
            style={{
              border: '1px solid color-mix(in srgb, #fff 14%, transparent)',
              padding: 24,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                marginBottom: 18,
              }}
            >
              <span
                style={{
                  fontSize: 11,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--color-neutral-500)',
                }}
              >
                {t('auth.panelKicker')}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-neutral-500)' }}>
                {formatDate(todayIso())}
              </span>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 16,
                marginBottom: 20,
              }}
            >
              <div>
                <div
                  style={{ fontSize: 11, color: 'var(--color-neutral-500)', marginBottom: 4 }}
                >
                  {t('dashboard.receivable')}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontWeight: 800,
                    fontSize: 22,
                    color: '#fff',
                  }}
                >
                  {formatMoney('1284.50')}
                </div>
              </div>
              <div>
                <div
                  style={{ fontSize: 11, color: 'var(--color-neutral-500)', marginBottom: 4 }}
                >
                  {t('dashboard.collectedToday')}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontWeight: 800,
                    fontSize: 22,
                    color: '#fff',
                  }}
                >
                  {formatMoney('185.00')}
                </div>
              </div>
            </div>
          </div>

          <p
            style={{
              fontSize: 15,
              lineHeight: 1.5,
              margin: '28px 0 8px',
              color: 'var(--color-neutral-200)',
            }}
          >
            {t('auth.quote')}
          </p>
          <p style={{ fontSize: 12.5, color: 'var(--color-neutral-500)', margin: 0 }}>
            {t('auth.quoteAuthor')}
          </p>
          <p style={{ fontSize: 12, color: 'var(--color-neutral-600)', marginTop: 24 }}>
            {t('auth.demoHint')}
          </p>
        </div>
      </div>
    </div>
      <ForgotPasswordDialog open={forgotOpen} onClose={() => setForgotOpen(false)} />
    </>
  )
}

function ForgotPasswordDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation()
  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-label={t('auth.forgotTitle')}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="dialog-title">{t('auth.forgotTitle')}</div>
        <div className="dialog-body">
          <p style={{ margin: '0 0 10px' }}>{t('auth.forgotBody')}</p>
          <pre
            style={{
              margin: '0 0 10px',
              padding: '10px 12px',
              borderRadius: 6,
              background: 'var(--color-surface)',
              fontSize: 12.5,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            uv run python scripts/reset_password.py admin@prestameami.pe NuevaClave123
          </pre>
          <p className="muted" style={{ margin: 0, fontSize: 13 }}>
            {t('auth.forgotNote')}
          </p>
        </div>
        <div className="dialog-actions">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  )
}
