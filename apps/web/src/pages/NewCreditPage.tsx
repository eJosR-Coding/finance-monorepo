/**
 * Credit simulator + granting.
 *
 * The schedule is NEVER computed here. The form gathers terms, the backend
 * returns the French schedule, and this screen only formats it. That's the
 * whole point: one engine, no drifting copies of the math.
 */

import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Field } from '@/components/Field'
import { PageHeader } from '@/components/PageHeader'
import { Segmented } from '@/components/Segmented'
import { Dialog } from '@/components/Dialog'
import { InlineError } from '@/components/States'
import { StatusTag } from '@/components/Tag'
import { ClientPicker } from '@/components/ClientPicker'
import { useToast } from '@/features/ui/ToastContext'
import { useClient, useConfig, useInvalidateAll } from '@/hooks/queries'
import { useSingleSubmit } from '@/hooks/useSingleSubmit'
import { translateError } from '@/lib/errors'
import { formatDate, formatMoney, todayIso } from '@/lib/format'
import { creditsApi } from '@/services/api'
import type { ClientListItem, CreditTerms, GraceType, Simulation } from '@/types/api'

interface FormState {
  amount: string
  startDate: string
  termDays: string
  installments: string
  frequency: string
  rateType: 'TEA' | 'TNA'
  annualRate: string
  graceType: GraceType
  graceDays: string
}

type Errors = Partial<Record<keyof FormState, string>>

export function NewCreditPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { notify } = useToast()
  const invalidateAll = useInvalidateAll()
  const [searchParams] = useSearchParams()
  const { data: config } = useConfig()
  const submitOnce = useSingleSubmit()

  const presetClientId = Number(searchParams.get('clientId') ?? '0')
  const { data: presetClient } = useClient(presetClientId)

  const [client, setClient] = useState<ClientListItem | null>(null)
  const [form, setForm] = useState<FormState>({
    amount: '140.00',
    startDate: todayIso(),
    termDays: '14',
    installments: '2',
    frequency: '7',
    rateType: 'TEA',
    annualRate: '40.00',
    graceType: 'none',
    graceDays: '0',
  })
  const [errors, setErrors] = useState<Errors>({})
  const [simulation, setSimulation] = useState<Simulation | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  // Arriving from a client's page preselects them.
  useEffect(() => {
    if (presetClient !== undefined && client === null) setClient(presetClient)
  }, [presetClient, client])

  // Default the rate to whatever the backend suggests.
  useEffect(() => {
    if (config !== undefined) {
      setForm((current) => ({ ...current, annualRate: config.default_annual_rate }))
    }
  }, [config])

  const maxAmount = config?.max_credit_amount ?? '200.00'
  const maxTerm = config?.max_term_days ?? 14
  const lateRate = simulation?.late_monthly_rate_percent ?? config?.late_monthly_rate_percent ?? '2.00'
  const blocked = client?.credit_status === 'blocked'

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: undefined }))
    setSimulation(null) // terms changed, the old schedule is stale
  }

  const validate = (): boolean => {
    const found: Errors = {}
    const amount = Number(form.amount)
    const term = Number(form.termDays)
    const installments = Number(form.installments)
    const frequency = Number(form.frequency)
    const grace = form.graceType === 'none' ? 0 : Number(form.graceDays)

    if (!Number.isFinite(amount) || amount <= 0) found.amount = t('validation.amountPositive')
    else if (amount > Number(maxAmount)) {
      found.amount = t('validation.amountMax', { amount: formatMoney(maxAmount) })
    }
    if (!Number.isFinite(term) || term < 1 || term > maxTerm) {
      found.termDays = t('validation.termRange', { max: maxTerm })
    }
    if (!Number.isFinite(installments) || installments < 1) {
      found.installments = t('validation.installmentsMin')
    }
    if (!Number.isFinite(frequency) || frequency < 1) found.frequency = t('validation.frequencyMin')
    if (Number(form.annualRate) < 0) found.annualRate = t('validation.rateNegative')

    const lastDay = grace + installments * frequency
    if (Number.isFinite(lastDay) && lastDay > term) {
      found.installments = t('validation.scheduleExceedsTerm', { days: lastDay, term })
    }

    setErrors(found)
    return Object.keys(found).length === 0
  }

  const terms = useMemo<CreditTerms | null>(() => {
    if (client === null) return null
    return {
      client_id: client.id,
      amount: form.amount,
      rate_type: form.rateType,
      annual_rate: form.annualRate,
      start_date: form.startDate,
      term_days: Number(form.termDays),
      installments_count: Number(form.installments),
      payment_frequency_days: Number(form.frequency),
      grace_type: form.graceType,
      grace_days: form.graceType === 'none' ? 0 : Number(form.graceDays),
    }
  }, [client, form])

  const simulateMutation = useMutation({
    mutationFn: () => {
      const payload = {
        client_id: client?.id ?? null,
        amount: form.amount,
        rate_type: form.rateType,
        annual_rate: form.annualRate,
        start_date: form.startDate,
        term_days: Number(form.termDays),
        installments_count: Number(form.installments),
        payment_frequency_days: Number(form.frequency),
        grace_type: form.graceType,
        grace_days: form.graceType === 'none' ? 0 : Number(form.graceDays),
      }
      return creditsApi.simulate(payload)
    },
    onSuccess: setSimulation,
    onError: (caught) => {
      setSimulation(null)
      setApiError(translateError(caught, t))
    },
  })

  const createMutation = useMutation({
    mutationFn: (payload: CreditTerms) => creditsApi.create(payload),
    onSuccess: (credit) => {
      invalidateAll()
      notify(t('newCredit.success'))
      navigate(`/creditos/${credit.id}`)
    },
    onError: (caught) => {
      setConfirmOpen(false)
      setApiError(translateError(caught, t))
    },
  })

  const onSimulate = () => {
    setApiError(null)
    if (!validate()) return
    simulateMutation.mutate()
  }

  const onConfirm = () => {
    if (terms === null) {
      setApiError(t('newCredit.selectClient'))
      return
    }
    submitOnce(() => createMutation.mutateAsync(terms))
  }

  return (
    <>
      <PageHeader title={t('newCredit.title')} subtitle={t('newCredit.subtitle')} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.3fr) minmax(300px, 1fr)',
          gap: 40,
          alignItems: 'start',
        }}
      >
        <div>
          <p className="sectitle">{t('newCredit.sectionClient')}</p>
          <Field label={t('newCredit.client')}>
            <ClientPicker selected={client} onSelect={setClient} />
          </Field>
          {client !== null && (
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
              <StatusTag status={client.credit_status} />
              {blocked && (
                <span style={{ fontSize: 12.5, color: 'var(--color-accent-700)', fontWeight: 600 }}>
                  {t('clientDetail.blockedNotice')}
                </span>
              )}
            </div>
          )}

          <div className="hr" style={{ marginTop: 28 }} />
          <p className="sectitle">{t('newCredit.sectionTerms')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Field
              label={t('newCredit.amount')}
              htmlFor="amount"
              error={errors.amount}
              hint={t('newCredit.maxAmount', { amount: formatMoney(maxAmount) })}
            >
              <input
                id="amount"
                className={errors.amount ? 'input input-invalid' : 'input'}
                inputMode="decimal"
                value={form.amount}
                onChange={(event) => set('amount', event.target.value)}
              />
            </Field>
            <Field label={t('newCredit.startDate')} htmlFor="startDate">
              <input
                id="startDate"
                type="date"
                className="input"
                value={form.startDate}
                onChange={(event) => set('startDate', event.target.value)}
              />
            </Field>
          </div>

          <div
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginTop: 16 }}
          >
            <Field
              label={t('newCredit.term')}
              htmlFor="termDays"
              error={errors.termDays}
              hint={t('newCredit.maxTerm', { days: maxTerm })}
            >
              <input
                id="termDays"
                className={errors.termDays ? 'input input-invalid' : 'input'}
                inputMode="numeric"
                value={form.termDays}
                onChange={(event) => set('termDays', event.target.value)}
              />
            </Field>
            <Field
              label={t('newCredit.installments')}
              htmlFor="installments"
              error={errors.installments}
            >
              <input
                id="installments"
                className={errors.installments ? 'input input-invalid' : 'input'}
                inputMode="numeric"
                value={form.installments}
                onChange={(event) => set('installments', event.target.value)}
              />
            </Field>
            <Field
              label={t('newCredit.frequency')}
              htmlFor="frequency"
              error={errors.frequency}
              hint={t('newCredit.frequencySuffix', { days: form.frequency })}
            >
              <input
                id="frequency"
                className={errors.frequency ? 'input input-invalid' : 'input'}
                inputMode="numeric"
                value={form.frequency}
                onChange={(event) => set('frequency', event.target.value)}
              />
            </Field>
          </div>

          <div className="hr" style={{ marginTop: 24 }} />
          <p className="sectitle">{t('newCredit.sectionRate')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Field label={t('newCredit.rateType')} htmlFor="rateType" tip={t('newCredit.rateTypeTip')}>
              <select
                id="rateType"
                className="input"
                value={form.rateType}
                onChange={(event) => set('rateType', event.target.value as 'TEA' | 'TNA')}
              >
                <option value="TEA">TEA</option>
                <option value="TNA">TNA</option>
              </select>
            </Field>
            <Field label={`${t('newCredit.rate')} (%)`} htmlFor="annualRate" error={errors.annualRate}>
              <input
                id="annualRate"
                className={errors.annualRate ? 'input input-invalid' : 'input'}
                inputMode="decimal"
                value={form.annualRate}
                onChange={(event) => set('annualRate', event.target.value)}
              />
            </Field>
          </div>

          <div className="hr" style={{ marginTop: 24 }} />
          <p className="sectitle">{t('newCredit.sectionGrace')}</p>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <Segmented
              ariaLabel={t('newCredit.sectionGrace')}
              value={form.graceType}
              onChange={(value) => set('graceType', value)}
              options={[
                { value: 'none', label: t('grace.none') },
                { value: 'partial', label: t('grace.partial') },
                { value: 'total', label: t('grace.total') },
              ]}
            />
            {form.graceType !== 'none' && (
              <Field label={t('newCredit.graceDays')} htmlFor="graceDays" tip={t('newCredit.graceTip')}>
                <input
                  id="graceDays"
                  className="input"
                  inputMode="numeric"
                  style={{ width: 120 }}
                  value={form.graceDays}
                  onChange={(event) => set('graceDays', event.target.value)}
                />
              </Field>
            )}
          </div>

          <div className="hr" style={{ marginTop: 24 }} />
          <p className="sectitle">{t('newCredit.sectionLate')}</p>
          <Field
            label={t('newCredit.lateRate')}
            tip={t('newCredit.lateRateTip')}
            className="max-w-[260px]"
          >
            <input
              className="input"
              value={t('newCredit.lateRateValue', { value: lateRate })}
              readOnly
              disabled
            />
          </Field>

          <div style={{ display: 'flex', gap: 12, marginTop: 28 }}>
            <Link to="/creditos" className="btn btn-secondary">
              {t('common.cancel')}
            </Link>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onSimulate}
              disabled={simulateMutation.isPending}
            >
              {simulateMutation.isPending ? t('newCredit.simulating') : t('newCredit.simulate')}
            </button>
          </div>

          {apiError !== null && <InlineError message={apiError} />}
        </div>

        <div style={{ position: 'sticky', top: 88 }}>
          <div className="card elev-md" style={{ padding: 20 }}>
            <p className="sectitle" style={{ marginBottom: 16 }}>
              {t('newCredit.summary')}
            </p>

            {simulation === null ? (
              <p className="muted" style={{ fontSize: 13, margin: 0 }}>
                {t('newCredit.emptyState')}
              </p>
            ) : (
              <>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 14,
                    marginBottom: 16,
                  }}
                >
                  <SummaryItem label={t('newCredit.capital')} value={formatMoney(simulation.amount)} />
                  <SummaryItem
                    label={t('newCredit.termLabel')}
                    value={`${simulation.term_days} ${t('common.days')}`}
                  />
                  <SummaryItem
                    label={t('newCredit.installmentsLabel')}
                    value={String(simulation.installments_count)}
                  />
                  <SummaryItem
                    label={t('newCredit.periodicRate')}
                    value={`${simulation.periodic_rate_percent} %`}
                  />
                </div>

                <div className="hr" style={{ margin: '12px 0' }} />

                <Row
                  label={t('newCredit.estimatedInstallment')}
                  value={formatMoney(simulation.installment_amount)}
                  emphasis
                />
                <Row
                  label={t('newCredit.totalInterest')}
                  value={formatMoney(simulation.total_interest)}
                />
                <Row
                  label={t('newCredit.totalPayment')}
                  value={formatMoney(simulation.total_payment)}
                />
                <Row label={t('newCredit.tcea')} value={`${simulation.tcea} %`} tip={t('newCredit.tceaTip')} />

                <div className="hr" style={{ margin: '14px 0' }} />
                <p className="sectitle" style={{ marginBottom: 10 }}>
                  {t('newCredit.schedule')}
                </p>
                <table className="table" style={{ fontSize: 12.5 }}>
                  <thead>
                    <tr>
                      <th>{t('newCredit.columns.number')}</th>
                      <th>{t('newCredit.columns.date')}</th>
                      <th>{t('newCredit.columns.interest')}</th>
                      <th>{t('newCredit.columns.capital')}</th>
                      <th>{t('newCredit.columns.installment')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simulation.schedule.map((row) => (
                      <tr key={row.installment_number}>
                        <td>{row.installment_number}</td>
                        <td>{formatDate(row.due_date)}</td>
                        <td className="num">{formatMoney(row.interest)}</td>
                        <td className="num">{formatMoney(row.amortization)}</td>
                        <td className="num">{formatMoney(row.installment)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 12.5,
                    opacity: 0.65,
                    margin: '10px 0 20px',
                  }}
                >
                  <span>{t('newCredit.finalBalance')}</span>
                  <span style={{ fontWeight: 700 }}>{formatMoney(simulation.final_balance)}</span>
                </div>

                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  disabled={client === null || blocked || createMutation.isPending}
                  onClick={() => setConfirmOpen(true)}
                >
                  {createMutation.isPending ? t('newCredit.confirming') : t('newCredit.confirm')}
                </button>
                {client === null && (
                  <p className="field-hint" style={{ textAlign: 'center' }}>
                    {t('newCredit.selectClient')}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <Dialog
        open={confirmOpen}
        title={t('newCredit.confirmTitle')}
        body={t('newCredit.confirmBody', {
          amount: formatMoney(simulation?.amount ?? form.amount),
          client: client?.full_name ?? '',
          count: simulation?.installments_count ?? Number(form.installments),
        })}
        confirmLabel={t('newCredit.confirm')}
        cancelLabel={t('common.cancel')}
        busy={createMutation.isPending}
        onConfirm={onConfirm}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  )
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 11, opacity: 0.55 }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: 15 }}>{value}</div>
    </div>
  )
}

function Row({
  label,
  value,
  emphasis = false,
  tip,
}: {
  label: string
  value: string
  emphasis?: boolean
  tip?: string
}) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: emphasis ? 10 : 6,
      }}
    >
      <span style={{ fontSize: 13, opacity: 0.65 }} title={tip}>
        {label}
      </span>
      <span
        style={
          emphasis
            ? { fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 22 }
            : { fontSize: 13, fontWeight: 700 }
        }
      >
        {value}
      </span>
    </div>
  )
}
