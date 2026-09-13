/**
 * Turns an ApiError into a message the user can actually read.
 *
 * The backend sends a stable `code` plus a Spanish fallback `message`. We look
 * the code up in the catalog and feed `details` in as interpolation values, so
 * "El monto maximo permitido es S/ {{max_amount}}." fills itself in.
 */

import type { TFunction } from 'i18next'

import { ApiError } from '@/services/http'

export function translateError(error: unknown, t: TFunction): string {
  if (error instanceof ApiError) {
    return t(`errors.${error.code}`, {
      ...error.details,
      defaultValue: error.message,
    })
  }
  if (error instanceof Error && error.message !== '') return error.message
  return t('common.error')
}

export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}
