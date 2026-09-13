/**
 * System parameters, read-only.
 *
 * The comp shows editable inputs here, but the ERD has no settings table and
 * inventing one to make a form work would put the docs and the database at
 * odds. These values live in the backend config and are shown as reference.
 */

import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import { PageHeader } from '@/components/PageHeader'
import { CardsSkeleton, ErrorState } from '@/components/States'
import { useAuth } from '@/features/auth/AuthContext'
import { useConfig } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatMoney } from '@/lib/format'

export function SettingsPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const { data: config, isLoading, isError, error, refetch } = useConfig()

  if (isError) {
    return <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
  }
  if (isLoading || config === undefined) return <CardsSkeleton count={3} />

  return (
    <div style={{ maxWidth: 900 }}>
      <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'var(--color-surface)',
          padding: '12px 16px',
          marginBottom: 28,
          fontSize: 13,
        }}
      >
        <Icon name="info" size={16} />
        {t('settings.readOnlyNotice')}
      </div>

      <p className="sectitle">{t('settings.limits')}</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <ReadOnly label={t('settings.maxAmount')} value={formatMoney(config.max_credit_amount)} />
        <ReadOnly
          label={t('settings.maxTerm')}
          value={`${config.max_term_days} ${t('common.days')}`}
        />
      </div>

      <div className="hr" />
      <p className="sectitle">{t('settings.rates')}</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <ReadOnly label={t('settings.defaultRate')} value={`${config.default_annual_rate} %`} />
        <ReadOnly
          label={t('settings.lateRate')}
          value={`${config.late_monthly_rate_percent} % / 30 ${t('common.days')}`}
        />
        <ReadOnly
          label={t('settings.daysPerYear')}
          value={`${config.days_per_year} ${t('common.days')}`}
        />
        <ReadOnly
          label={t('settings.ratePrecision')}
          value={String(config.rate_percent_decimals)}
        />
      </div>

      <div className="hr" />
      <p className="sectitle">{t('settings.rulesTitle')}</p>
      <div style={{ maxWidth: 340, marginBottom: 8 }}>
        <ReadOnly
          label={t('settings.blockAfter')}
          value={t('settings.blockAfterValue', { count: config.overdue_installments_to_block })}
        />
      </div>
      <p className="field-hint" style={{ marginBottom: 24 }}>
        {t('settings.blockNote')}
      </p>

      <div className="hr" />
      <p className="sectitle">{t('settings.account')}</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <ReadOnly label={t('settings.name')} value={user?.name ?? '—'} />
        <ReadOnly label={t('settings.email')} value={user?.email ?? '—'} />
      </div>
    </div>
  )
}

function ReadOnly({ label, value }: { label: string; value: string }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input className="input" value={value} readOnly disabled />
    </div>
  )
}
