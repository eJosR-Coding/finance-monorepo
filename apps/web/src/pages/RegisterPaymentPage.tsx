/**
 * Record a payment.
 *
 * The allocation preview comes from the API (`/payments/preview`) - the same
 * code path that will actually apply the money. No client-side guessing about
 * how the waterfall splits.
 */

import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Dialog } from '@/components/Dialog'
import { Field } from '@/components/Field'
import { Breadcrumb } from '@/components/PageHeader'
import { Segmented } from '@/components/Segmented'
import { CardsSkeleton, ErrorState, InlineError } from '@/components/States'
import { useToast } from '@/features/ui/ToastContext'
import { useCredit, useInvalidateAll } from '@/hooks/queries'
import { useSingleSubmit } from '@/hooks/useSingleSubmit'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { paymentsApi } from '@/services/api'
import type { PaymentMethod, PaymentPreview } from '@/types/api'

const METHODS: readonly { value: PaymentMethod; labelKey: string }[] = [
  { value: 'cash', labelKey: 'payment.methodCash' },
  { value: 'yape', labelKey: 'payment.methodYape' },
  { value: 'plin', labelKey: 'payment.methodPlin' },
  { value: 'transfer', labelKey: 'payment.methodTransfer' },
]

export function RegisterPaymentPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { notify } = useToast()
  const invalidateAll = useInvalidateAll()
  const submitOnce = useSingleSubmit()
  const { creditId } = useParams()
  const [searchParams] = useSearchParams()
  const id = Number(creditId)

  const { data: credit, isLoading, isError, error, refetch } = useCredit(id)

  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState<PaymentMethod>('cash')
  const [date, setDate] = useState(todayIso())
  const [notes, setNotes] = useState('')
  const [preview, setPreview] = useState<PaymentPreview | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  // Target installment: the one asked for in the URL, else the oldest unpaid.
  const targetInstallment = useMemo(() => {
    if (credit === undefined) return null
    const requested = Number(searchParams.get('installmentId') ?? '0')
    const pending = credit.installments.filter((item) => item.status !== 'paid')
    return pending.find((item) => item.id === requested) ?? pending[0] ?? null
  }, [credit, searchParams])

  // Prefill with exactly what the installment owes - the common case.
  useEffect(() => {
    if (targetInstallment !== null && amount === '') {
      setAmount(targetInstallment.outstanding_amount)
    }
  }, [targetInstallment, amount])

  const previewMutation = useMutation({
    mutationFn: () =>
      paymentsApi.preview(id, {
        amount_received: amount,
        payment_date: date,
        installment_id: targetInstallment?.id ?? null,
      }),
    onSuccess: setPreview,
    onError: (caught) => {
      setPreview(null)
      setApiError(translateError(caught, t))
    },
  })

  // Re-ask the API whenever the amount, date or target changes.
  useEffect(() => {
    setApiError(null)
    const parsed = Number(amount)
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setPreview(null)
      return
    }
    const timer = window.setTimeout(() => previewMutation.mutate(), 280)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amount, date, targetInstallment?.id])

  const createMutation = useMutation({
    mutationFn: () =>
      paymentsApi.create(id, {
        amount_received: amount,
        payment_method: method,
        payment_date: date,
        installment_id: targetInstallment?.id ?? null,
        notes: notes.trim() === '' ? null : notes.trim(),
      }),
    onSuccess: () => {
      invalidateAll()
      notify(t('payment.success'))
      navigate(`/creditos/${id}`)
    },
    onError: (caught) => {
      setConfirmOpen(false)
      setApiError(translateError(caught, t))
    },
  })

  if (isError) {
    return <ErrorState message={translateError(error, t)} onRetry={() => void refetch()} />
  }
  if (isLoading || credit === undefined) return <CardsSkeleton count={4} />

  const outcomeTag = () => {
    if (preview === null) return null
    if (preview.days_late > 0) {
      return <span className="tag tag-accent">{t('payment.outcomeOverdue')}</span>
    }
    if (preview.outcome === 'surplus') {
      return <span className="tag tag-outline">{t('payment.outcomeSurplus')}</span>
    }
    if (preview.outcome === 'partial') {
      return <span className="tag tag-warning">{t('payment.outcomePartial')}</span>
    }
    return <span className="tag tag-success">{t('payment.outcomeExact')}</span>
  }

  const canSubmit =
    preview !== null && Number(amount) > 0 && !createMutation.isPending && credit.status !== 'paid'

  return (
    <div style={{ maxWidth: 1100 }}>
      <Breadcrumb>
        <Link to={`/clientes/${credit.client_id}`}>{credit.client_name}</Link> /{' '}
        <Link to={`/creditos/${credit.id}`}>{credit.code}</Link> / {t('payment.title')}
      </Breadcrumb>

      <h1 style={{ fontSize: 26, marginBottom: 6 }}>{t('payment.title')}</h1>
      <p style={{ fontSize: 14, opacity: 0.62, margin: '0 0 20px' }}>{t('payment.subtitle')}</p>

      <div
        style={{
          display: 'flex',
          gap: 28,
          flexWrap: 'wrap',
          padding: '16px 20px',
          background: 'var(--color-surface)',
          marginBottom: 32,
          fontSize: 13.5,
        }}
      >
        <ContextItem label={t('payment.client')} value={credit.client_name} />
        <ContextItem label={t('payment.credit')} value={credit.code} />
        <ContextItem
          label={t('payment.installment')}
          value={
            targetInstallment === null
              ? '—'
              : `${targetInstallment.installment_number} ${t('common.of')} ${credit.installments_count}`
          }
        />
        <ContextItem
          label={t('payment.due')}
          value={targetInstallment === null ? '—' : formatDate(targetInstallment.due_date)}
        />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 40,
          alignItems: 'start',
        }}
      >
        <div>
          <p className="sectitle">{t('payment.section')}</p>

          <Field label={t('payment.date')} htmlFor="date" className="mb-4">
            <input
              id="date"
              type="date"
              className="input"
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </Field>

          <Field label={t('payment.amount')} htmlFor="amount" className="mb-4">
            <input
              id="amount"
              className="input"
              inputMode="decimal"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </Field>

          <Field label={t('payment.method')} className="mb-4">
            <Segmented
              ariaLabel={t('payment.method')}
              value={method}
              onChange={setMethod}
              options={METHODS.map((item) => ({ value: item.value, label: t(item.labelKey) }))}
            />
          </Field>

          <Field label={t('payment.notes')} htmlFor="notes">
            <textarea
              id="notes"
              className="input"
              rows={3}
              maxLength={500}
              placeholder={t('payment.notesPlaceholder')}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
          </Field>

          <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
            <Link to={`/creditos/${credit.id}`} className="btn btn-secondary">
              {t('common.cancel')}
            </Link>
            <button
              type="button"
              className="btn btn-primary"
              disabled={!canSubmit}
              onClick={() => setConfirmOpen(true)}
            >
              {createMutation.isPending ? t('payment.submitting') : t('payment.submit')}
            </button>
          </div>

          {apiError !== null && <InlineError message={apiError} />}
        </div>

        <div>
          <div className="card elev-md" style={{ padding: 20 }}>
            <p className="sectitle" style={{ marginBottom: 14 }}>
              {t('payment.allocation')}
            </p>

            {preview === null ? (
              <p className="muted" style={{ fontSize: 13, margin: 0 }}>
                {t('payment.fillAmount')}
              </p>
            ) : (
              <>
                <Line label={t('payment.dueAmount')} value={formatMoney(preview.due_amount)} bold />
                <div className="hr" style={{ margin: '10px 0' }} />
                <Line
                  label={t('payment.lateInterest')}
                  value={formatMoney(preview.late_interest_amount)}
                />
                <Line
                  label={t('payment.compensatoryInterest')}
                  value={formatMoney(preview.compensatory_interest_amount)}
                />
                <Line label={t('payment.principal')} value={formatMoney(preview.principal_amount)} />
                <div className="hr" style={{ margin: '10px 0' }} />
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    marginBottom: 8,
                  }}
                >
                  <span style={{ fontSize: 13, opacity: 0.65 }}>{t('payment.totalApplied')}</span>
                  <span
                    style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 20 }}
                  >
                    {formatMoney(preview.total_applied)}
                  </span>
                </div>
                <Line
                  label={t('payment.balanceAfter')}
                  value={formatMoney(preview.remaining_balance)}
                  bold
                />
                <div
                  style={{
                    display: 'flex',
                    gap: 8,
                    alignItems: 'center',
                    marginTop: 14,
                    flexWrap: 'wrap',
                  }}
                >
                  {outcomeTag()}
                  {preview.days_late > 0 && (
                    <span className="muted" style={{ fontSize: 12 }}>
                      {t('payment.daysLate', { count: preview.days_late })}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>

          <p className="field-hint" style={{ marginTop: 14 }}>
            {t('payment.waterfall')}
          </p>
        </div>
      </div>

      <Dialog
        open={confirmOpen}
        title={t('payment.confirmTitle')}
        body={t('payment.confirmBody', {
          amount: formatMoney(preview?.total_applied ?? amount),
          client: credit.client_name,
        })}
        confirmLabel={t('payment.submit')}
        cancelLabel={t('common.cancel')}
        busy={createMutation.isPending}
        onConfirm={() => submitOnce(() => createMutation.mutateAsync())}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  )
}

function ContextItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span style={{ opacity: 0.55 }}>{label}</span>
      <div style={{ fontWeight: 700 }}>{value}</div>
    </div>
  )
}

function Line({ label, value, bold = false }: { label: string; value: string; bold?: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
      <span style={{ fontSize: 13, opacity: 0.65 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: bold ? 700 : 400 }}>{value}</span>
    </div>
  )
}
