/**
 * Thin fetch wrapper. Owns the token, the JSON plumbing and error shaping, so
 * no component ever touches `fetch` directly.
 */

import type { ApiErrorBody } from '@/types/api'

const BASE_URL = '/api'
const TOKEN_KEY = 'prestameami.token'

export class ApiError extends Error {
  readonly code: string
  readonly status: number
  readonly details: Record<string, unknown>

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.details = body.details ?? {}
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token === null) localStorage.removeItem(TOKEN_KEY)
  else localStorage.setItem(TOKEN_KEY, token)
}

type Method = 'GET' | 'POST' | 'PATCH' | 'DELETE'

async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const token = getToken()

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(token === null ? {} : { Authorization: `Bearer ${token}` }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
  } catch {
    // fetch REJECTS when the server is unreachable, it does not return a
    // response, so the !response.ok path below never sees this case. Without
    // this catch the user would read a raw "Failed to fetch" in English.
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: 'No se pudo contactar al servidor. Revisa que la API este levantada.',
      details: {},
    })
  }

  if (response.status === 204) return undefined as T

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const fallback: ApiErrorBody = {
      code: 'NETWORK_ERROR',
      message: 'No se pudo contactar al servidor.',
      details: {},
    }
    throw new ApiError(response.status, (payload as ApiErrorBody | null) ?? fallback)
  }

  return payload as T
}

export const http = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body ?? {}),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
}

/** Builds `?a=1&b=2`, skipping empty values so the URL stays clean. */
export function query(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === '') continue
    search.set(key, String(value))
  }
  const serialized = search.toString()
  return serialized === '' ? '' : `?${serialized}`
}
