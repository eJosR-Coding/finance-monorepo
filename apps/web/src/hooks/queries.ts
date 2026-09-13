/**
 * TanStack Query wrappers. Query keys live here so invalidation after a
 * mutation can't drift out of sync with the fetchers.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'

import { clientsApi, configApi, creditsApi, dashboardApi, paymentsApi } from '@/services/api'

export const queryKeys = {
  config: ['config'] as const,
  dashboard: ['dashboard'] as const,
  overdue: ['overdue'] as const,
  clients: (params: Record<string, unknown>) => ['clients', params] as const,
  client: (id: number) => ['client', id] as const,
  credits: (params: Record<string, unknown>) => ['credits', params] as const,
  credit: (id: number) => ['credit', id] as const,
  payments: (creditId: number) => ['payments', creditId] as const,
  allPayments: ['payments', 'all'] as const,
}

export function useConfig() {
  return useQuery({
    queryKey: queryKeys.config,
    queryFn: configApi.get,
    staleTime: Infinity, // product limits don't move while you're using the app
  })
}

export function useDashboard() {
  return useQuery({ queryKey: queryKeys.dashboard, queryFn: dashboardApi.get })
}

export function useOverdue() {
  return useQuery({ queryKey: queryKeys.overdue, queryFn: dashboardApi.overdue })
}

export function useClients(params: { search?: string; status?: string; sort?: string }) {
  return useQuery({
    queryKey: queryKeys.clients(params),
    queryFn: () => clientsApi.list(params),
  })
}

export function useClient(id: number) {
  return useQuery({
    queryKey: queryKeys.client(id),
    queryFn: () => clientsApi.get(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useCredits(params: { client_id?: number; status?: string } = {}) {
  return useQuery({
    queryKey: queryKeys.credits(params),
    queryFn: () => creditsApi.list(params),
  })
}

export function useCredit(id: number) {
  return useQuery({
    queryKey: queryKeys.credit(id),
    queryFn: () => creditsApi.get(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function usePayments(creditId: number) {
  return useQuery({
    queryKey: queryKeys.payments(creditId),
    queryFn: () => paymentsApi.list(creditId),
    enabled: Number.isFinite(creditId) && creditId > 0,
  })
}

export function useAllPayments() {
  return useQuery({ queryKey: queryKeys.allPayments, queryFn: paymentsApi.listAll })
}

/** After any write, everything money-related is suspect. Nuke it all. */
export function useInvalidateAll() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries()
  }
}
