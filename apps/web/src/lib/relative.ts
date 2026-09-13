/** "Hoy" / "Ayer" / "Hace 3 dias" for last-activity columns. */

import type { TFunction } from 'i18next'

import { daysBetween, formatDate, todayIso } from '@/lib/format'

export function relativeDay(value: string | null | undefined, t: TFunction): string {
  if (!value) return '—'
  const [datePart = ''] = value.split('T')
  const delta = daysBetween(todayIso(), datePart)
  if (delta <= 0) return t('common.today')
  if (delta === 1) return t('common.yesterday')
  if (delta < 30) return t('common.daysAgo', { count: delta })
  return formatDate(datePart)
}
