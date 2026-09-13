/** Status pill. One mapping from domain status to visual tone, used everywhere. */

import { useTranslation } from 'react-i18next'

import type { ClientCreditStatus, CreditStatus, InstallmentStatus } from '@/types/api'

type AnyStatus = ClientCreditStatus | CreditStatus | InstallmentStatus

const TONE: Record<AnyStatus, string> = {
  enabled: 'tag-success',
  paid: 'tag-success',
  active: 'tag-warning',
  pending: 'tag-warning',
  blocked: 'tag-accent',
  overdue: 'tag-accent',
}

export function StatusTag({ status }: { status: AnyStatus }) {
  const { t } = useTranslation()
  return <span className={`tag ${TONE[status]}`}>{t(`status.${status}`)}</span>
}
