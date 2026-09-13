/** Every collection across all credits, newest first. */

import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { PageHeader } from '@/components/PageHeader'
import { EmptyState, ErrorState, TableSkeleton } from '@/components/States'
import { useAllPayments } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney } from '@/lib/format'

export function PaymentsPage() {
  const { t } = useTranslation()
  const { data = [], isLoading, isError, error, refetch } = useAllPayments()

  return (
    <>
      <PageHeader title={t('payments.title')} subtitle={t('payments.subtitle')} />

      {isError && <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />}
      {isLoading && <TableSkeleton rows={5} columns={8} />}

      {!isLoading && !isError && data.length === 0 && (
        <EmptyState message={t('payments.empty')} />
      )}

      {data.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>{t('payments.columns.date')}</th>
                <th>{t('payments.columns.client')}</th>
                <th>{t('payments.columns.credit')}</th>
                <th>{t('payments.columns.amount')}</th>
                <th>{t('payments.columns.late')}</th>
                <th>{t('payments.columns.interest')}</th>
                <th>{t('payments.columns.capital')}</th>
                <th>{t('payments.columns.balance')}</th>
                <th>{t('payments.columns.method')}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((payment) => (
                <tr key={payment.id}>
                  <td>{formatDate(payment.payment_date)}</td>
                  <td>
                    <Link to={`/clientes/${payment.client_id}`}>{payment.client_name}</Link>
                  </td>
                  <td>
                    <Link to={`/creditos/${payment.credit_id}`}>{payment.credit_code}</Link>
                  </td>
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
