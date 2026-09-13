/** Credit terms + full amortization schedule + payment history. */

import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import { Breadcrumb } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { CardsSkeleton, EmptyState, ErrorState } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { useCredit, usePayments } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney } from '@/lib/format'

export function CreditDetailPage() {
  const { t } = useTranslation()
  const { creditId } = useParams()
  const id = Number(creditId)

  const { data: credit, isLoading, isError, error, refetch } = useCredit(id)
  const { data: payments = [] } = usePayments(id)

  if (isError) {
    return <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
  }
  if (isLoading || credit === undefined) return <CardsSkeleton count={5} />

  const graceLabel =
    credit.grace_type === 'none'
      ? t('common.none')
      : `${t(`grace.${credit.grace_type}`)} · ${credit.grace_days} ${t('common.days')}`

  return (
    <>
      <Breadcrumb>
        <Link to="/clientes">{t('nav.clients')}</Link> /{' '}
        <Link to={`/clientes/${credit.client_id}`}>{credit.client_name}</Link> /{' '}
        {t('creditDetail.title', { code: credit.code })}
      </Breadcrumb>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
          flexWrap: 'wrap',
          marginBottom: 6,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 style={{ fontSize: 24 }}>{t('creditDetail.title', { code: credit.code })}</h1>
          <StatusTag status={credit.status} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {credit.status !== 'paid' && (
            <Link to={`/creditos/${credit.id}/pagos/nuevo`} className="btn btn-primary">
              {t('creditDetail.registerPayment')}
            </Link>
          )}
          <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
            <Icon name="download" size={14} />
            {t('creditDetail.download')}
          </button>
        </div>
      </div>
      <p style={{ fontSize: 13, opacity: 0.55, margin: '0 0 28px' }}>
        {t('creditDetail.createdOn', { date: formatDate(credit.created_at) })}
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 16,
          marginBottom: 36,
        }}
      >
        <StatCard label={t('creditDetail.capital')} value={formatMoney(credit.amount)} size="sm" />
        <StatCard
          label={t('creditDetail.balance')}
          value={formatMoney(credit.outstanding_balance)}
          size="sm"
          tone={credit.status === 'overdue' ? 'alert' : 'default'}
        />
        <StatCard
          label={t('creditDetail.installment')}
          value={formatMoney(credit.installment_amount)}
          size="sm"
        />
        <StatCard
          label={t('creditDetail.totalPayment')}
          value={formatMoney(credit.total_payment)}
          size="sm"
        />
        <StatCard
          label={t('creditDetail.nextDue')}
          value={formatDate(credit.next_due_date)}
          size="sm"
        />
      </div>

      <h2 style={{ fontSize: 18, marginBottom: 16 }}>{t('creditDetail.terms')}</h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 16,
          marginBottom: 32,
        }}
      >
        <Term label={t('creditDetail.rateType')} value={credit.rate_type} />
        <Term label={t('creditDetail.annualRate')} value={`${credit.annual_rate} %`} />
        <Term label={t('creditDetail.periodicRate')} value={`${credit.periodic_rate_percent} %`} />
        <Term label={t('creditDetail.term')} value={`${credit.term_days} ${t('common.days')}`} />
        <Term label={t('creditDetail.installments')} value={String(credit.installments_count)} />
        <Term
          label={t('creditDetail.frequency')}
          value={`${credit.payment_frequency_days} ${t('common.days')}`}
        />
        <Term label={t('creditDetail.grace')} value={graceLabel} />
        <Term label="TCEA" value={`${credit.tcea} %`} />
        <Term
          label={t('creditDetail.lateRate')}
          value={`${credit.late_monthly_rate_percent} % ${t('common.of')} 30 ${t('common.days')}`}
        />
      </div>

      <div className="hr" />

      <h2 style={{ fontSize: 18, margin: '24px 0 16px' }}>{t('creditDetail.schedule')}</h2>
      <div style={{ overflowX: 'auto' }}>
        <table className="table" style={{ marginBottom: 36 }}>
          <thead>
            <tr>
              <th>{t('creditDetail.columns.number')}</th>
              <th>{t('creditDetail.columns.date')}</th>
              <th>{t('creditDetail.columns.opening')}</th>
              <th>{t('creditDetail.columns.interest')}</th>
              <th>{t('creditDetail.columns.amortization')}</th>
              <th>{t('creditDetail.columns.installment')}</th>
              <th>{t('creditDetail.columns.closing')}</th>
              <th>{t('creditDetail.columns.status')}</th>
            </tr>
          </thead>
          <tbody>
            {credit.installments.map((row) => (
              <tr key={row.id}>
                <td>{row.installment_number}</td>
                <td>{formatDate(row.due_date)}</td>
                <td className="num">{formatMoney(row.opening_balance)}</td>
                <td className="num">{formatMoney(row.interest_amount)}</td>
                <td className="num">{formatMoney(row.amortization_amount)}</td>
                <td className="num">{formatMoney(row.installment_amount)}</td>
                <td className="num">{formatMoney(row.closing_balance)}</td>
                <td>
                  <StatusTag status={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 style={{ fontSize: 18, marginBottom: 16 }}>{t('creditDetail.paymentHistory')}</h2>
      {payments.length === 0 ? (
        <EmptyState
          message={t('creditDetail.noPayments')}
          action={
            credit.status === 'paid' ? undefined : (
              <Link to={`/creditos/${credit.id}/pagos/nuevo`} className="btn btn-primary">
                {t('creditDetail.firstPayment')}
              </Link>
            )
          }
        />
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>{t('creditDetail.columns.date')}</th>
                <th>{t('creditDetail.columns.amount')}</th>
                <th>{t('creditDetail.columns.late')}</th>
                <th>{t('creditDetail.columns.interest')}</th>
                <th>{t('creditDetail.columns.capital')}</th>
                <th>{t('creditDetail.columns.balance')}</th>
                <th>{t('creditDetail.columns.method')}</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{formatDate(payment.payment_date)}</td>
                  <td className="num">{formatMoney(payment.amount_received)}</td>
                  <td className="num">{formatMoney(payment.late_interest_amount)}</td>
                  <td className="num">{formatMoney(payment.compensatory_interest_amount)}</td>
                  <td className="num">{formatMoney(payment.principal_amount)}</td>
                  <td className="num">{formatMoney(payment.remaining_balance)}</td>
                  <td>{t(`method.${payment.payment_method}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function Term({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', opacity: 0.5 }}>
        {label}
      </div>
      <div style={{ fontWeight: 700, fontSize: 14.5, marginTop: 2 }}>{value}</div>
    </div>
  )
}
