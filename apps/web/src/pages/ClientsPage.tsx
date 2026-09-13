/** Client list with search, status filter and sort. */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Avatar } from '@/components/Avatar'
import { Icon } from '@/components/Icon'
import { PageHeader } from '@/components/PageHeader'
import { EmptyState, ErrorState, TableSkeleton } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { useClients } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { formatMoney } from '@/lib/format'
import { relativeDay } from '@/lib/relative'

export function ClientsPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [sort, setSort] = useState('recent')

  const { data, isLoading, isError, error, refetch } = useClients({ search, status, sort })
  const items = data?.items ?? []
  const hasFilters = search !== '' || status !== ''

  return (
    <>
      <PageHeader
        title={t('clients.title')}
        subtitle={t('clients.subtitle')}
        actions={
          <Link to="/clientes/nuevo" className="btn btn-primary">
            <Icon name="plus" size={14} />
            {t('clients.new')}
          </Link>
        }
      />

      <div
        style={{
          display: 'flex',
          gap: 12,
          alignItems: 'center',
          marginBottom: 20,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ position: 'relative', flex: '1 1 260px' }}>
          <span style={{ position: 'absolute', left: 10, top: 11, opacity: 0.5 }}>
            <Icon name="search" size={15} />
          </span>
          <input
            className="input"
            style={{ paddingLeft: 32 }}
            placeholder={t('clients.searchPlaceholder')}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label={t('clients.searchPlaceholder')}
          />
        </div>
        <select
          className="input"
          style={{ width: 'auto', minWidth: 150 }}
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          aria-label={t('clients.columns.status')}
        >
          <option value="">{t('clients.filterAll')}</option>
          <option value="enabled">{t('clients.filterEnabled')}</option>
          <option value="blocked">{t('clients.filterBlocked')}</option>
        </select>
        <select
          className="input"
          style={{ width: 'auto', minWidth: 170 }}
          value={sort}
          onChange={(event) => setSort(event.target.value)}
          aria-label={t('clients.sortRecent')}
        >
          <option value="recent">{t('clients.sortRecent')}</option>
          <option value="debt">{t('clients.sortDebt')}</option>
        </select>
      </div>

      {isError && (
        <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
      )}

      {isLoading && <TableSkeleton rows={5} columns={7} />}

      {data !== undefined && items.length === 0 && (
        <EmptyState
          icon="users"
          message={hasFilters ? t('clients.empty') : t('clients.emptyAll')}
          action={
            hasFilters ? undefined : (
              <Link to="/clientes/nuevo" className="btn btn-primary">
                {t('clients.new')}
              </Link>
            )
          }
        />
      )}

      {items.length > 0 && (
        <>
          <table className="table">
            <thead>
              <tr>
                <th>{t('clients.columns.client')}</th>
                <th>{t('clients.columns.dni')}</th>
                <th>{t('clients.columns.phone')}</th>
                <th>{t('clients.columns.activeCredit')}</th>
                <th>{t('clients.columns.balance')}</th>
                <th>{t('clients.columns.status')}</th>
                <th>{t('clients.columns.lastMovement')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((client) => (
                <tr key={client.id}>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <Avatar initials={client.initials} />
                      {client.full_name}
                    </span>
                  </td>
                  <td>{client.dni}</td>
                  <td>{client.phone}</td>
                  <td>{t('clients.creditCount', { count: client.active_credits })}</td>
                  <td className="num">{formatMoney(client.outstanding_balance)}</td>
                  <td>
                    <StatusTag status={client.credit_status} />
                  </td>
                  <td>{relativeDay(client.last_movement_at, t)}</td>
                  <td>
                    <Link to={`/clientes/${client.id}`}>{t('clients.viewClient')}</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 20, fontSize: 13, opacity: 0.6 }}>
            {t('clients.showing', { count: items.length, total: data?.total ?? items.length })}
          </div>
        </>
      )}
    </>
  )
}
