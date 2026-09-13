/**
 * Mirror of the FastAPI schemas. Money and rates arrive as STRINGS on purpose:
 * they keep exact decimal precision, so we format them, never do math on them.
 * Any arithmetic on these belongs in the backend, full stop.
 */

export type ClientCreditStatus = 'enabled' | 'blocked'
export type RateType = 'TNA' | 'TEA'
export type GraceType = 'none' | 'partial' | 'total'
export type CreditStatus = 'active' | 'paid' | 'overdue'
export type InstallmentStatus = 'pending' | 'paid' | 'overdue'
export type PaymentMethod = 'cash' | 'yape' | 'plin' | 'transfer'

export interface ApiErrorBody {
  code: string
  message: string
  details: Record<string, unknown>
}

export interface User {
  id: number
  name: string
  email: string
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Client {
  id: number
  dni: string
  first_name: string
  last_name: string
  full_name: string
  initials: string
  phone: string
  address: string
  credit_status: ClientCreditStatus
  created_at: string
  updated_at: string
}

export interface ClientListItem extends Client {
  active_credits: number
  outstanding_balance: string
  last_movement_at: string | null
}

export interface ActivityItem {
  date: string
  type: 'client_created' | 'credit_created' | 'payment_registered'
  title: string
  amount: string | null
  credit_id: number | null
}

export interface ClientDetail extends ClientListItem {
  total_paid: string
  last_payment_date: string | null
  credits: CreditListItem[]
  payments: Payment[]
  activity: ActivityItem[]
}

export interface ClientListResponse {
  items: ClientListItem[]
  total: number
}

export interface ClientPayload {
  dni: string
  first_name: string
  last_name: string
  phone: string
  address: string
}

export interface CreditTerms {
  client_id: number
  amount: string
  rate_type: RateType
  annual_rate: string
  start_date: string
  term_days: number
  installments_count: number
  payment_frequency_days: number
  grace_type: GraceType
  grace_days: number
}

export type SimulationPayload = Omit<CreditTerms, 'client_id'> & { client_id: number | null }

export interface ScheduleRow {
  installment_number: number
  due_date: string
  opening_balance: string
  interest: string
  amortization: string
  installment: string
  closing_balance: string
}

export interface Simulation {
  amount: string
  financed_principal: string
  rate_type: RateType
  annual_rate: string
  periodic_rate: string
  periodic_rate_percent: string
  installment_amount: string
  total_interest: string
  total_payment: string
  final_balance: string
  tcea: string
  term_days: number
  installments_count: number
  payment_frequency_days: number
  grace_type: GraceType
  grace_days: number
  late_monthly_rate_percent: string
  schedule: ScheduleRow[]
}

export interface Installment {
  id: number
  installment_number: number
  due_date: string
  opening_balance: string
  interest_amount: string
  amortization_amount: string
  installment_amount: string
  closing_balance: string
  status: InstallmentStatus
  paid_amount: string
  outstanding_amount: string
  days_late: number
}

export interface Credit {
  id: number
  code: string
  client_id: number
  amount: string
  start_date: string
  term_days: number
  rate_type: RateType
  annual_rate: string
  periodic_rate: string
  periodic_rate_percent: string
  installments_count: number
  payment_frequency_days: number
  grace_type: GraceType
  grace_days: number
  total_interest: string
  total_payment: string
  outstanding_balance: string
  status: CreditStatus
  created_at: string
}

export interface CreditListItem extends Credit {
  client_name: string
  next_due_date: string | null
}

export interface CreditDetail extends CreditListItem {
  client_dni: string
  client_credit_status: ClientCreditStatus
  installment_amount: string
  tcea: string
  late_monthly_rate_percent: string
  installments: Installment[]
}

export interface CreditListResponse {
  items: CreditListItem[]
  total: number
}

export interface Payment {
  id: number
  credit_id: number
  installment_id: number
  payment_date: string
  amount_received: string
  late_interest_amount: string
  compensatory_interest_amount: string
  principal_amount: string
  remaining_balance: string
  payment_method: PaymentMethod
  notes: string | null
  created_at: string
}

export interface PaymentListItem extends Payment {
  credit_code: string
  client_id: number
  client_name: string
}

export interface PaymentAllocation {
  installment_id: number
  installment_number: number
  late_interest_amount: string
  compensatory_interest_amount: string
  principal_amount: string
  total_applied: string
  installment_status: InstallmentStatus
}

export interface PaymentPayload {
  amount_received: string
  payment_method?: PaymentMethod
  payment_date?: string | null
  installment_id?: number | null
  notes?: string | null
}

export type PaymentOutcome = 'exact' | 'partial' | 'surplus'

export interface PaymentPreview {
  amount_received: string
  due_amount: string
  late_interest_amount: string
  compensatory_interest_amount: string
  principal_amount: string
  total_applied: string
  remaining_balance: string
  unapplied_amount: string
  outcome: PaymentOutcome
  days_late: number
  allocations: PaymentAllocation[]
}

export interface PaymentResult {
  credit_id: number
  payment_date: string
  amount_received: string
  late_interest_amount: string
  compensatory_interest_amount: string
  principal_amount: string
  remaining_balance: string
  credit_status: CreditStatus
  client_credit_status: ClientCreditStatus
  allocations: PaymentAllocation[]
  payments: Payment[]
}

export interface UpcomingInstallment {
  credit_id: number
  credit_code: string
  installment_id: number
  installment_number: number
  client_id: number
  client_name: string
  due_date: string
  amount: string
  status: InstallmentStatus
  days_late: number
}

export interface RecentCredit {
  credit_id: number
  credit_code: string
  client_id: number
  client_name: string
  amount: string
  term_days: number
  installments_count: number
  total_payment: string
  status: CreditStatus
}

export interface Dashboard {
  active_credits: number
  outstanding_total: string
  collected_today: string
  payments_today: number
  blocked_clients: number
  overdue_installments: number
  overdue_balance: string
  week_expected_total: string
  week_expected_count: number
  upcoming_installments: UpcomingInstallment[]
  recent_credits: RecentCredit[]
}

export interface OverdueRow {
  client_id: number
  client_name: string
  client_credit_status: ClientCreditStatus
  credit_id: number
  credit_code: string
  due_date: string
  days_late: number
  overdue_balance: string
  late_interest: string
  credit_status: CreditStatus
  last_payment_date: string | null
}

export interface OverdueReport {
  blocked_clients: number
  overdue_balance: string
  overdue_installments: number
  rows: OverdueRow[]
}

export interface AppConfig {
  currency: string
  currency_symbol: string
  max_credit_amount: string
  min_term_days: number
  max_term_days: number
  days_per_year: number
  money_decimals: number
  rate_percent_decimals: number
  default_annual_rate: string
  late_monthly_rate_percent: string
  overdue_installments_to_block: number
}
