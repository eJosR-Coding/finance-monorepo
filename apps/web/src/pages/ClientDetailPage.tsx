/** Client file: KPIs, tabs (credits / payments / activity) and a timeline. */

import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Avatar } from '@/components/Avatar'
import { Icon } from '@/components/Icon'
import { Breadcrumb } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { CardsSkeleton, ErrorState } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { useClient } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney } from '@/lib/format'

type Tab = 'credits' | 'payments' | 'activity'

export function ClientDetailPage() {
  const { t } = useTranslation()
  const { clientId } = useParams()
  const id = Number(clientId)
  const [tab, setTab] = useState<Tab>('credits')

  const { data: client, isLoading, isError, error, refetch } = useClient(id)

  if (isError) {
    return <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
  }
  if (isLoading || client === undefined) return <CardsSkeleton count={4} />

  const blocked = client.credit_status === 'blocked'

  return (
    <>
      <Breadcrumb>
        <Link to="/clientes">{t('nav.clients')}</Link> / {client.full_name}
      </Breadcrumb>

      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: 24,
          gap: 24,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Avatar initials={client.initials} size={52} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h1 style={{ fontSize: 22 }}>{client.full_name}</h1>
              <StatusTag status={client.credit_status} />
            </div>
            <div style={{ fontSize: 13, opacity: 0.6 }}>
              DNI {client.dni} · {client.phone} · {client.address}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Link
            to={`/creditos/nuevo?clientId=${client.id}`}
            className="btn btn-primary"
            aria-disabled={blocked}
            style={blocked ? { opacity: 0.45, pointerEvents: 'none' } : undefined}
          >
            <Icon name="plus" size={14} />
            {t('clientDetail.newCredit')}
          </Link>
        </div>
      </div>

      {blocked && (
        <div
          role="status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: 'var(--color-accent-100)',
            color: 'var(--color-accent-800)',
            padding: '12px 16px',
            marginBottom: 24,
            fontSize: 13.5,
            fontWeight: 600,
          }}
        >
          <Icon name="info" size={16} />
          {t('clientDetail.blockedNotice')}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginBottom: 32,
        }}
      >
        <StatCard
          label={t('clientDetail.balance')}
          value={formatMoney(client.outstanding_balance)}
          size="sm"
        />
        <StatCard label={t('clientDetail.activeCredits')} value={client.active_credits} size="sm" />
        <StatCard
          label={t('clientDetail.totalPaid')}
          value={formatMoney(client.total_paid)}
          size="sm"
        />
        <StatCard
          label={t('clientDetail.lastPayment')}
          value={formatDate(client.last_payment_date)}
          size="sm"
        />
      </div>

      <div
        role="tablist"
        style={{
          display: 'flex',
          gap: 24,
          borderBottom: '2px solid var(--divider)',
          marginBottom: 24,
        }}
      >
        {(['credits', 'payments', 'activity'] as const).map((key) => (
          <button
            key={key}
            type="button"
            role="tab"
            className="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
          >
            {t(`clientDetail.tab${key.charAt(0).toUpperCase()}${key.slice(1)}`)}
          </button>
        ))}
      </div>

      {tab === 'credits' &&
        (client.credits.length === 0 ? (
          <p className="muted" style={{ fontSize: 14 }}>
            {t('clientDetail.noCredits')}
          </p>
        ) : (
          <table className="table" style={{ marginBottom: 40 }}>
            <thead>
              <tr>
                <th>{t('clientDetail.columns.id')}</th>
                <th>{t('clientDetail.columns.date')}</th>
                <th>{t('clientDetail.columns.amount')}</th>
                <th>{t('clientDetail.columns.installments')}</th>
                <th>{t('clientDetail.columns.balance')}</th>
                <th>{t('clientDetail.columns.status')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {client.credits.map((credit) => (
                <tr key={credit.id}>
                  <td>{credit.code}</td>
                  <td>{formatDate(credit.start_date)}</td>
                  <td className="num">{formatMoney(credit.amount)}</td>
                  <td className="num">{credit.installments_count}</td>
                  <td className="num">{formatMoney(credit.outstanding_balance)}</td>
                  <td>
                    <StatusTag status={credit.status} />
                  </td>
                  <td>
                    <Link to={`/creditos/${credit.id}`}>{t('common.view')}</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

      {tab === 'payments' &&
        (client.payments.length === 0 ? (
          <p className="muted" style={{ fontSize: 14 }}>
            {t('clientDetail.noPayments')}
          </p>
        ) : (
          <table className="table" style={{ marginBottom: 40 }}>
            <thead>
              <tr>
                <th>{t('clientDetail.columns.date')}</th>
                <th>{t('clientDetail.columns.credit')}</th>
                <th>{t('clientDetail.columns.amount')}</th>
                <th>{t('clientDetail.columns.method')}</th>
              </tr>
            </thead>
            <tbody>
              {client.payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{formatDate(payment.payment_date)}</td>
                  <td>
                    <Link to={`/creditos/${payment.credit_id}`}>
                      CR-{String(payment.credit_id).padStart(4, '0')}
                    </Link>
                  </td>
                  <td className="num">{formatMoney(payment.amount_received)}</td>
                  <td>{t(`method.${payment.payment_method}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

      {tab === 'activity' && (
        <p className="muted" style={{ fontSize: 14, marginBottom: 40 }}>
          {t('clientDetail.noActivity')}
        </p>
      )}

      <h2 style={{ fontSize: 18, marginBottom: 16 }}>{t('clientDetail.history')}</h2>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {client.activity.map((item, index) => (
          <div
            key={`${item.type}-${item.date}-${index}`}
            style={{
              display: 'flex',
              gap: 16,
              paddingBottom: index === client.activity.length - 1 ? 0 : 20,
              borderLeft:
                index === client.activity.length - 1 ? 'none' : '2px solid var(--divider)',
              marginLeft: 5,
              paddingLeft: 20,
              position: 'relative',
            }}
          >
            <span
              style={{
                position: 'absolute',
                left: -6,
                top: 2,
                width: 10,
                height: 10,
                background:
                  index === 0 ? 'var(--color-accent)' : 'var(--color-neutral-400)',
              }}
            />
            <div>
              <div style={{ fontSize: 12.5, opacity: 0.55, marginBottom: 2 }}>
                {formatDate(item.date)}
              </div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{t(`activity.${item.type}`)}</div>
              {item.amount !== null && (
                <div style={{ fontSize: 13, opacity: 0.7 }}>{formatMoney(item.amount)}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
