/** Business overview: KPIs, upcoming collections, latest credits. */

import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import { PageHeader } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { CardsSkeleton, EmptyState, ErrorState, TableSkeleton } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { translateError } from '@/lib/errors'
import { daysBetween, formatDate, formatMoney, todayIso } from '@/lib/format'
import { useDashboard } from '@/hooks/queries'

export function DashboardPage() {
  const { t } = useTranslation()
  const { data, isLoading, isError, error, refetch } = useDashboard()

  const dueLabel = (dueDate: string) => {
    const delta = daysBetween(dueDate, todayIso())
    if (delta === 0) return t('common.today')
    return formatDate(dueDate)
  }

  return (
    <>
      <PageHeader
        title={t('dashboard.title')}
        subtitle={t('dashboard.subtitle')}
        actions={
          <Link to="/creditos/nuevo" className="btn btn-primary">
            <Icon name="plus" size={14} />
            {t('dashboard.newCredit')}
          </Link>
        }
      />

      {isError && (
        <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
      )}

      {isLoading && <CardsSkeleton count={4} />}

      {data !== undefined && (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 16,
              marginBottom: 32,
            }}
          >
            <StatCard
              label={t('dashboard.activeCredits')}
              value={data.active_credits}
              meta={t('dashboard.activeCreditsMeta', {
                count: data.upcoming_installments.length,
              })}
            />
            <StatCard
              label={t('dashboard.receivable')}
              value={formatMoney(data.outstanding_total)}
              meta={t('dashboard.overdueInstallments', { count: data.overdue_installments })}
            />
            <StatCard
              label={t('dashboard.collectedToday')}
              value={formatMoney(data.collected_today)}
              meta={t('dashboard.collectedTodayMeta', { count: data.payments_today })}
            />
            <StatCard
              label={t('dashboard.blockedClients')}
              value={data.blocked_clients}
              meta={t('dashboard.blockedClientsMeta')}
              tone={data.blocked_clients > 0 ? 'alert' : 'default'}
            />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 2fr) minmax(240px, 1fr)',
              gap: 32,
              alignItems: 'start',
            }}
          >
            <div>
              <SectionTitle title={t('dashboard.upcoming')} to="/morosos" label={t('dashboard.viewAll')} />
              {data.upcoming_installments.length === 0 ? (
                <EmptyState
                  message={t('dashboard.empty')}
                  action={
                    <Link to="/creditos/nuevo" className="btn btn-primary">
                      {t('dashboard.emptyCta')}
                    </Link>
                  }
                />
              ) : (
                <table className="table" style={{ marginBottom: 36 }}>
                  <thead>
                    <tr>
                      <th>{t('dashboard.columns.client')}</th>
                      <th>{t('dashboard.columns.installment')}</th>
                      <th>{t('dashboard.columns.due')}</th>
                      <th>{t('dashboard.columns.status')}</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.upcoming_installments.map((item) => (
                      <tr key={item.installment_id}>
                        <td>{item.client_name}</td>
                        <td className="num">{formatMoney(item.amount)}</td>
                        <td>{dueLabel(item.due_date)}</td>
                        <td>
                          <StatusTag status={item.status} />
                        </td>
                        <td>
                          <Link to={`/creditos/${item.credit_id}/pagos/nuevo`}>
                            {item.status === 'overdue'
                              ? t('dashboard.collect')
                              : t('common.view')}
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <SectionTitle
                title={t('dashboard.recentCredits')}
                to="/creditos"
                label={t('dashboard.viewAll')}
              />
              {data.recent_credits.length === 0 ? (
                <p className="muted" style={{ fontSize: 14 }}>
                  {t('dashboard.empty')}
                </p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>{t('dashboard.columns.client')}</th>
                      <th>{t('dashboard.columns.capital')}</th>
                      <th>{t('dashboard.columns.term')}</th>
                      <th>{t('dashboard.columns.installments')}</th>
                      <th>{t('dashboard.columns.total')}</th>
                      <th>{t('dashboard.columns.status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_credits.map((credit) => (
                      <tr key={credit.credit_id}>
                        <td>
                          <Link to={`/creditos/${credit.credit_id}`}>{credit.client_name}</Link>
                        </td>
                        <td className="num">{formatMoney(credit.amount)}</td>
                        <td>
                          {credit.term_days} {t('common.days')}
                        </td>
                        <td className="num">{credit.installments_count}</td>
                        <td className="num">{formatMoney(credit.total_payment)}</td>
                        <td>
                          <StatusTag status={credit.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <h2 style={{ fontSize: 18, margin: 0 }}>{t('dashboard.attention')}</h2>
              <div className="card elev-sm">
                <div
                  className="card-kicker"
                  style={{
                    color:
                      data.overdue_installments > 0
                        ? 'var(--color-accent-700)'
                        : 'var(--color-accent)',
                  }}
                >
                  {t('dashboard.overdueInstallments', { count: data.overdue_installments })}
                </div>
                <p style={{ margin: 0, fontSize: 13 }}>
                  {t('dashboard.overdueAmount', {
                    amount: formatMoney(data.overdue_balance),
                  })}
                </p>
                <Link to="/morosos" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>
                  {t('dashboard.goToOverdue')}
                </Link>
              </div>
              <div className="card elev-sm">
                <div className="card-kicker">
                  {t('dashboard.weekCollections', { count: data.week_expected_count })}
                </div>
                <p style={{ margin: 0, fontSize: 13 }}>
                  {t('dashboard.weekExpected', {
                    amount: formatMoney(data.week_expected_total),
                  })}
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {isLoading && (
        <div style={{ marginTop: 32 }}>
          <TableSkeleton rows={3} columns={5} />
        </div>
      )}
    </>
  )
}

function SectionTitle({ title, to, label }: { title: string; to: string; label: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 14,
      }}
    >
      <h2 style={{ fontSize: 18, margin: 0 }}>{title}</h2>
      <Link to={to} style={{ fontSize: 13 }}>
        {label}
      </Link>
    </div>
  )
}
