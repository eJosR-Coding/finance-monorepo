"""Dashboard, delinquency and system-parameter schemas."""

from datetime import date

from pydantic import BaseModel

from app.schemas.common import Money, Percent


class UpcomingInstallment(BaseModel):
    credit_id: int
    credit_code: str
    installment_id: int
    installment_number: int
    client_id: int
    client_name: str
    due_date: date
    amount: Money
    status: str
    days_late: int


class RecentCredit(BaseModel):
    credit_id: int
    credit_code: str
    client_id: int
    client_name: str
    amount: Money
    term_days: int
    installments_count: int
    total_payment: Money
    status: str


class DashboardResponse(BaseModel):
    active_credits: int
    outstanding_total: Money
    collected_today: Money
    payments_today: int
    blocked_clients: int
    overdue_installments: int
    overdue_balance: Money
    week_expected_total: Money
    week_expected_count: int
    upcoming_installments: list[UpcomingInstallment]
    recent_credits: list[RecentCredit]


class OverdueRow(BaseModel):
    client_id: int
    client_name: str
    client_credit_status: str
    credit_id: int
    credit_code: str
    due_date: date
    days_late: int
    overdue_balance: Money
    late_interest: Money
    credit_status: str
    last_payment_date: date | None


class OverdueResponse(BaseModel):
    blocked_clients: int
    overdue_balance: Money
    overdue_installments: int
    rows: list[OverdueRow]


class ConfigResponse(BaseModel):
    """Product parameters. Read-only from the UI."""

    currency: str
    currency_symbol: str
    max_credit_amount: Money
    min_term_days: int
    max_term_days: int
    days_per_year: int
    money_decimals: int
    rate_percent_decimals: int
    default_annual_rate: Percent
    late_monthly_rate_percent: Percent
    overdue_installments_to_block: int
