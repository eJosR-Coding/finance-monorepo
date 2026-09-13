/** The shell every screen except Login lives in: sidebar + topbar + outlet. */

import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Avatar } from '@/components/Avatar'
import { Dialog } from '@/components/Dialog'
import { Icon } from '@/components/Icon'
import type { IconName } from '@/components/Icon'
import { useAuth } from '@/features/auth/AuthContext'
import { changeLanguage } from '@/lib/i18n'
import type { Language } from '@/lib/i18n'
import { initialsOf } from '@/lib/format'

const NAV: { to: string; icon: IconName; key: string }[] = [
  { to: '/dashboard', icon: 'dashboard', key: 'nav.dashboard' },
  { to: '/clientes', icon: 'users', key: 'nav.clients' },
  { to: '/creditos', icon: 'credit-card', key: 'nav.credits' },
  { to: '/pagos', icon: 'wallet', key: 'nav.payments' },
  { to: '/morosos', icon: 'alert-triangle', key: 'nav.overdue' },
  { to: '/configuracion', icon: 'settings', key: 'nav.settings' },
]

export function AppLayout() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [logoutOpen, setLogoutOpen] = useState(false)

  const name = user?.name ?? ''
  const initials = initialsOf(name)

  const confirmLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const toggleLanguage = () => {
    changeLanguage((i18n.language.startsWith('en') ? 'es' : 'en') as Language)
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-bg)' }}>
      <aside
        style={{
          width: 230,
          flex: 'none',
          background: 'var(--color-neutral-900)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          position: 'sticky',
          top: 0,
        }}
      >
        <div
          style={{ padding: '22px 22px 20px', display: 'flex', alignItems: 'center', gap: 9 }}
        >
          <span
            style={{ width: 22, height: 22, background: 'var(--color-accent)', flex: 'none' }}
          />
          <span
            style={{
              fontFamily: 'var(--font-heading)',
              fontWeight: 800,
              fontSize: 16.5,
              color: '#fff',
            }}
          >
            {t('common.appName')}
            <span style={{ color: 'var(--color-accent-400)' }}>{t('common.appSuffix')}</span>
          </span>
        </div>

        <nav
          style={{
            flex: 1,
            padding: '8px 12px',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'navlink active' : 'navlink')}
            >
              <Icon name={item.icon} size={17} />
              {t(item.key)}
            </NavLink>
          ))}
        </nav>

        <div
          style={{
            padding: '14px 16px',
            borderTop: '1px solid color-mix(in srgb, #fff 12%, transparent)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Avatar initials={initials} size={32} tone="accent" />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: 12.5,
                fontWeight: 700,
                color: '#fff',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {name}
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-neutral-500)' }}>{t('nav.role')}</div>
          </div>
          <button
            type="button"
            aria-label={t('nav.logout')}
            onClick={() => setLogoutOpen(true)}
            style={{
              background: 'transparent',
              border: 0,
              color: 'var(--color-neutral-500)',
              cursor: 'pointer',
              padding: 6,
              display: 'flex',
            }}
          >
            <Icon name="log-out" size={16} />
          </button>
        </div>
      </aside>

      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            height: 64,
            flex: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            padding: '0 32px',
            borderBottom: '2px solid var(--divider)',
            position: 'sticky',
            top: 0,
            background: 'var(--color-bg)',
            zIndex: 5,
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 700 }}>{t('common.appName')}</span>
          <div
            style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              onClick={toggleLanguage}
              aria-label={t('common.language')}
              style={{ fontSize: 12, padding: '6px 10px', gap: 6 }}
            >
              <Icon name="globe" size={14} />
              {i18n.language.startsWith('en') ? 'EN' : 'ES'}
            </button>
            <button
              type="button"
              className="btn btn-icon btn-glass"
              aria-label={t('nav.notifications')}
            >
              <Icon name="bell" size={16} />
            </button>
            <div style={{ width: 1, height: 22, background: 'var(--divider)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar initials={initials} size={28} tone="dark" />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{name}</span>
            </div>
          </div>
        </header>

        <main style={{ flex: 1, padding: '32px 40px 72px', maxWidth: 1180, width: '100%' }}>
          <Outlet />
        </main>
      </div>

      <Dialog
        open={logoutOpen}
        title={t('logout.title')}
        body={t('logout.body')}
        confirmLabel={t('logout.confirm')}
        cancelLabel={t('common.cancel')}
        onConfirm={confirmLogout}
        onCancel={() => setLogoutOpen(false)}
      />
    </div>
  )
}
