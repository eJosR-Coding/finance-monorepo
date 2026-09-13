/**
 * Client registration.
 *
 * The comp also shows birth date, email and notes, but the academic ERD has no
 * columns for them - the database is the single source of truth, so those
 * fields are left out instead of faked.
 */

import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { Field } from '@/components/Field'
import { PageHeader } from '@/components/PageHeader'
import { InlineError } from '@/components/States'
import { useToast } from '@/features/ui/ToastContext'
import { useInvalidateAll } from '@/hooks/queries'
import { translateError } from '@/lib/errors'
import { clientsApi } from '@/services/api'
import type { ClientPayload } from '@/types/api'

type Errors = Partial<Record<keyof ClientPayload, string>>

const EMPTY: ClientPayload = {
  dni: '',
  first_name: '',
  last_name: '',
  phone: '',
  address: '',
}

export function NewClientPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { notify } = useToast()
  const invalidateAll = useInvalidateAll()

  const [form, setForm] = useState<ClientPayload>(EMPTY)
  const [errors, setErrors] = useState<Errors>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (payload: ClientPayload) => clientsApi.create(payload),
    onSuccess: (client) => {
      invalidateAll()
      notify(t('newClient.success'))
      navigate(`/clientes/${client.id}`)
    },
    onError: (caught) => setApiError(translateError(caught, t)),
  })

  const set = (key: keyof ClientPayload, value: string) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: undefined }))
  }

  const validate = (): boolean => {
    const found: Errors = {}
    if (form.first_name.trim() === '') found.first_name = t('validation.required')
    if (form.last_name.trim() === '') found.last_name = t('validation.required')
    if (form.address.trim() === '') found.address = t('validation.required')
    if (form.phone.trim().length < 6) found.phone = t('validation.phoneShort')
    if (form.dni.trim().length !== 8) found.dni = t('validation.dniLength')
    else if (!/^\d+$/.test(form.dni.trim())) found.dni = t('validation.dniDigits')
    setErrors(found)
    return Object.keys(found).length === 0
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    setApiError(null)
    if (!validate()) return
    mutation.mutate({
      dni: form.dni.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      phone: form.phone.trim(),
      address: form.address.trim(),
    })
  }

  return (
    <div style={{ maxWidth: 760 }}>
      <PageHeader title={t('newClient.title')} subtitle={t('newClient.subtitle')} />

      <form onSubmit={onSubmit} noValidate>
        <p className="sectitle">{t('newClient.personal')}</p>
        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}
        >
          <Field label={t('newClient.firstName')} htmlFor="first_name" error={errors.first_name}>
            <input
              id="first_name"
              className={errors.first_name ? 'input input-invalid' : 'input'}
              placeholder={t('newClient.firstNamePlaceholder')}
              value={form.first_name}
              onChange={(event) => set('first_name', event.target.value)}
            />
          </Field>
          <Field label={t('newClient.lastName')} htmlFor="last_name" error={errors.last_name}>
            <input
              id="last_name"
              className={errors.last_name ? 'input input-invalid' : 'input'}
              placeholder={t('newClient.lastNamePlaceholder')}
              value={form.last_name}
              onChange={(event) => set('last_name', event.target.value)}
            />
          </Field>
        </div>

        <Field
          label={t('newClient.dni')}
          htmlFor="dni"
          error={errors.dni}
          className="mb-6"
        >
          <input
            id="dni"
            className={errors.dni ? 'input input-invalid' : 'input'}
            placeholder={t('newClient.dniPlaceholder')}
            maxLength={8}
            inputMode="numeric"
            value={form.dni}
            onChange={(event) => set('dni', event.target.value.replace(/\D/g, ''))}
            style={{ maxWidth: 220 }}
          />
        </Field>

        <div className="hr" />
        <p className="sectitle">{t('newClient.contact')}</p>
        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}
        >
          <Field label={t('newClient.phone')} htmlFor="phone" error={errors.phone}>
            <input
              id="phone"
              className={errors.phone ? 'input input-invalid' : 'input'}
              placeholder={t('newClient.phonePlaceholder')}
              value={form.phone}
              onChange={(event) => set('phone', event.target.value)}
            />
          </Field>
          <Field label={t('newClient.address')} htmlFor="address" error={errors.address}>
            <input
              id="address"
              className={errors.address ? 'input input-invalid' : 'input'}
              placeholder={t('newClient.addressPlaceholder')}
              value={form.address}
              onChange={(event) => set('address', event.target.value)}
            />
          </Field>
        </div>

        <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
          <Link to="/clientes" className="btn btn-secondary">
            {t('common.cancel')}
          </Link>
          <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? t('newClient.submitting') : t('newClient.submit')}
          </button>
        </div>

        {apiError !== null && <InlineError message={apiError} />}
      </form>
    </div>
  )
}
