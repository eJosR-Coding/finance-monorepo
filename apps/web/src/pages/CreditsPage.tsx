/** Every credit granted, filterable by status. */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Icon } from '@/components/Icon'
import { PageHeader } from '@/components/PageHeader'
import { Segmented } from '@/components/Segmented'
import { EmptyState, ErrorState, TableSkeleton } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { useCredits } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney } from '@/lib/format'

type Filter = '' | 'active' | 'overdue' | 'paid'

export function CreditsPage() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<Filter>('')
  const { data, isLoading, isError, error, refetch } = useCredits(
    filter === '' ? {} : { status: filter },
  )
  const items = data?.items ?? []

  return (
    <>
      <PageHeader
        title={t('credits.title')}
        subtitle={t('credits.subtitle')}
        actions={
          <Link to="/creditos/nuevo" className="btn btn-primary">
            <Icon name="plus" size={14} />
            {t('dashboard.newCredit')}
          </Link>
        }
      />

      <div style={{ marginBottom: 20 }}>
        <Segmented
          ariaLabel={t('credits.title')}
          value={filter}
          onChange={setFilter}
          options={[
            { value: '', label: t('credits.filterAll') },
            { value: 'active', label: t('credits.filterActive') },
            { value: 'overdue', label: t('credits.filterOverdue') },
            { value: 'paid', label: t('credits.filterPaid') },
          ]}
        />
      </div>

      {isError && <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />}
      {isLoading && <TableSkeleton rows={5} columns={7} />}

      {data !== undefined && items.length === 0 && (
        <EmptyState
          icon="credit-card"
          message={t('credits.empty')}
          action={
            <Link to="/creditos/nuevo" className="btn btn-primary">
              {t('dashboard.newCredit')}
            </Link>
          }
        />
      )}

      {items.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>{t('credits.columns.code')}</th>
                <th>{t('credits.columns.client')}</th>
                <th>{t('credits.columns.date')}</th>
                <th>{t('credits.columns.capital')}</th>
                <th>{t('credits.columns.installments')}</th>
                <th>{t('credits.columns.balance')}</th>
                <th>{t('credits.columns.nextDue')}</th>
                <th>{t('credits.columns.status')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((credit) => (
                <tr key={credit.id}>
                  <td>
                    <Link to={`/creditos/${credit.id}`}>{credit.code}</Link>
                  </td>
                  <td>{credit.client_name}</td>
                  <td>{formatDate(credit.start_date)}</td>
                  <td className="num">{formatMoney(credit.amount)}</td>
                  <td className="num">{credit.installments_count}</td>
                  <td className="num">{formatMoney(credit.outstanding_balance)}</td>
                  <td>{formatDate(credit.next_due_date)}</td>
                  <td>
                    <StatusTag status={credit.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
