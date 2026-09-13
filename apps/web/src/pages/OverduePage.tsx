/** Overdue installments and the clients they blocked. */

import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import { PageHeader } from '@/components/PageHeader'
import { Segmented } from '@/components/Segmented'
import { CardsSkeleton, EmptyState, ErrorState } from '@/components/States'
import { StatCard } from '@/components/StatCard'
import { StatusTag } from '@/components/Tag'
import { useOverdue } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney } from '@/lib/format'

type Filter = 'all' | 'overdue' | 'blocked' | 'today'

export function OverduePage() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')

  const { data, isLoading, isError, error, refetch } = useOverdue()

  const rows = useMemo(() => {
    const all = data?.rows ?? []
    const term = search.trim().toLowerCase()
    return all.filter((row) => {
      if (term !== '' && !row.client_name.toLowerCase().includes(term)) return false
      if (filter === 'blocked') return row.client_credit_status === 'blocked'
      if (filter === 'overdue') return row.credit_status === 'overdue'
      if (filter === 'today') return row.days_late === 1
      return true
    })
  }, [data, filter, search])

  if (isError) {
    return <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
  }
  if (isLoading || data === undefined) return <CardsSkeleton count={3} />

  return (
    <>
      <PageHeader title={t('overdue.title')} subtitle={t('overdue.subtitle')} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginBottom: 28,
        }}
      >
        <StatCard label={t('overdue.blockedClients')} value={data.blocked_clients} />
        <StatCard
          label={t('overdue.overdueBalance')}
          value={formatMoney(data.overdue_balance)}
          tone="alert"
        />
        <StatCard label={t('overdue.overdueInstallments')} value={data.overdue_installments} />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2.4fr) minmax(220px, 1fr)',
          gap: 32,
          alignItems: 'start',
        }}
      >
        <div>
          <div
            style={{
              display: 'flex',
              gap: 12,
              alignItems: 'center',
              marginBottom: 20,
              flexWrap: 'wrap',
            }}
          >
            <Segmented
              ariaLabel={t('overdue.title')}
              value={filter}
              onChange={setFilter}
              options={[
                { value: 'all', label: t('overdue.filterAll') },
                { value: 'overdue', label: t('overdue.filterOverdue') },
                { value: 'blocked', label: t('overdue.filterBlocked') },
                { value: 'today', label: t('overdue.filterToday') },
              ]}
            />
            <div style={{ position: 'relative', flex: '1 1 200px' }}>
              <span style={{ position: 'absolute', left: 10, top: 11, opacity: 0.5 }}>
                <Icon name="search" size={15} />
              </span>
              <input
                className="input"
                style={{ paddingLeft: 32 }}
                placeholder={t('overdue.searchPlaceholder')}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label={t('overdue.searchPlaceholder')}
              />
            </div>
          </div>

          {rows.length === 0 ? (
            <EmptyState icon="check-circle" message={t('overdue.empty')} />
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('overdue.columns.client')}</th>
                    <th>{t('overdue.columns.credit')}</th>
                    <th>{t('overdue.columns.due')}</th>
                    <th>{t('overdue.columns.daysLate')}</th>
                    <th>{t('overdue.columns.balance')}</th>
                    <th>{t('overdue.columns.status')}</th>
                    <th>{t('overdue.columns.lastPayment')}</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={`${row.credit_id}-${row.due_date}`}>
                      <td>
                        <Link to={`/clientes/${row.client_id}`}>{row.client_name}</Link>
                      </td>
                      <td>{row.credit_code}</td>
                      <td>{formatDate(row.due_date)}</td>
                      <td className="num">
                        {row.days_late} {row.days_late === 1 ? t('common.day') : t('common.days')}
                      </td>
                      <td className="num">{formatMoney(row.overdue_balance)}</td>
                      <td>
                        <StatusTag status={row.client_credit_status} />
                      </td>
                      <td>{formatDate(row.last_payment_date)}</td>
                      <td>
                        <Link to={`/creditos/${row.credit_id}/pagos/nuevo`}>
                          {t('overdue.registerPayment')}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card" style={{ gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--color-accent-700)' }}>
              <Icon name="info" size={16} />
            </span>
            <div className="card-kicker" style={{ margin: 0 }}>
              {t('overdue.rule')}
            </div>
          </div>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>{t('overdue.ruleBody')}</p>
        </div>
      </div>
    </>
  )
}
