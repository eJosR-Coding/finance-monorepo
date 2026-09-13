/** One function per endpoint. Components call these, never `http` directly. */

import { http, query } from '@/services/http'
import type {
  AppConfig,
  Client,
  ClientDetail,
  ClientListResponse,
  ClientPayload,
  CreditDetail,
  CreditListResponse,
  CreditTerms,
  LoginResponse,
  OverdueReport,
  Payment,
  PaymentListItem,
  PaymentPayload,
  PaymentPreview,
  PaymentResult,
  Dashboard,
  SimulationPayload,
  Simulation,
  User,
} from '@/types/api'

export const authApi = {
  login: (email: string, password: string) =>
    http.post<LoginResponse>('/auth/login', { email, password }),
  me: () => http.get<User>('/auth/me'),
}

export const configApi = {
  get: () => http.get<AppConfig>('/config'),
}

export const clientsApi = {
  list: (params: { search?: string; status?: string; sort?: string }) =>
    http.get<ClientListResponse>(`/clients${query(params)}`),
  get: (id: number) => http.get<ClientDetail>(`/clients/${id}`),
  create: (payload: ClientPayload) => http.post<Client>('/clients', payload),
  update: (id: number, payload: Partial<ClientPayload>) =>
    http.patch<Client>(`/clients/${id}`, payload),
}

export const creditsApi = {
  simulate: (payload: SimulationPayload) => http.post<Simulation>('/credits/simulate', payload),
  create: (payload: CreditTerms) => http.post<CreditDetail>('/credits', payload),
  list: (params: { client_id?: number; status?: string } = {}) =>
    http.get<CreditListResponse>(`/credits${query(params)}`),
  get: (id: number) => http.get<CreditDetail>(`/credits/${id}`),
}

export const paymentsApi = {
  listAll: () => http.get<PaymentListItem[]>('/payments'),
  list: (creditId: number) => http.get<Payment[]>(`/credits/${creditId}/payments`),
  preview: (creditId: number, payload: PaymentPayload) =>
    http.post<PaymentPreview>(`/credits/${creditId}/payments/preview`, payload),
  create: (creditId: number, payload: PaymentPayload) =>
    http.post<PaymentResult>(`/credits/${creditId}/payments`, payload),
}

export const dashboardApi = {
  get: () => http.get<Dashboard>('/dashboard'),
  overdue: () => http.get<OverdueReport>('/overdue'),
}
