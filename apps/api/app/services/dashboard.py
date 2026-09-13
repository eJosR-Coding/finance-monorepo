"""Dashboard and delinquency ("morosos") read models."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core import clock
from app.core.enums import InstallmentStatus
from app.core.money import ZERO_MONEY, money
from app.repositories import clients as clients_repo
from app.repositories import credits as credits_repo
from app.repositories import payments as payments_repo
from app.schemas.dashboard import (
    DashboardResponse,
    OverdueResponse,
    OverdueRow,
    RecentCredit,
    UpcomingInstallment,
)
from app.services import balances, delinquency, finance

UPCOMING_LIMIT = 6
RECENT_CREDITS_LIMIT = 5


def build(session: Session, today: date | None = None) -> DashboardResponse:
    today = today or clock.today()
    delinquency.sync(session, today)
    session.commit()

    open_credits = credits_repo.list_open(session)
    pending = credits_repo.list_pending_installments(session)
    todays_payments = payments_repo.list_by_date(session, today)

    week_end = today + timedelta(days=7)
    this_week = [i for i in pending if today <= i.due_date <= week_end]
    overdue = [i for i in pending if i.status == InstallmentStatus.overdue]

    upcoming = [
        UpcomingInstallment(
            credit_id=i.credit_id,
            credit_code=i.credit.code,
            installment_id=i.id,
            installment_number=i.installment_number,
            client_id=i.credit.client_id,
            client_name=i.credit.client.full_name,
            due_date=i.due_date,
            amount=balances.outstanding_amount(i),
            status=i.status,
            days_late=delinquency.days_late(i, today),
        )
        for i in pending[:UPCOMING_LIMIT]
    ]

    recent = [
        RecentCredit(
            credit_id=c.id,
            credit_code=c.code,
            client_id=c.client_id,
            client_name=c.client.full_name,
            amount=c.amount,
            term_days=c.term_days,
            installments_count=c.installments_count,
            total_payment=c.total_payment,
            status=c.status,
        )
        for c in credits_repo.list_all(session)[:RECENT_CREDITS_LIMIT]
    ]

    return DashboardResponse(
        active_credits=len(open_credits),
        outstanding_total=money(
            sum((c.outstanding_balance for c in open_credits), ZERO_MONEY)
        ),
        collected_today=money(sum((p.amount_received for p in todays_payments), ZERO_MONEY)),
        payments_today=len(todays_payments),
        blocked_clients=clients_repo.count_blocked(session),
        overdue_installments=len(overdue),
        overdue_balance=money(
            sum((balances.outstanding_amount(i) for i in overdue), ZERO_MONEY)
        ),
        week_expected_total=money(
            sum((balances.outstanding_amount(i) for i in this_week), ZERO_MONEY)
        ),
        week_expected_count=len(this_week),
        upcoming_installments=upcoming,
        recent_credits=recent,
    )


def overdue_report(session: Session, today: date | None = None) -> OverdueResponse:
    """Everything the Morosos screen needs: one row per overdue installment."""
    today = today or clock.today()
    delinquency.sync(session, today)
    session.commit()

    rows: list[OverdueRow] = []
    for installment in credits_repo.list_pending_installments(session, until=today):
        if installment.due_date >= today:
            continue
        credit = installment.credit
        outstanding = balances.outstanding_amount(installment)
        days = delinquency.days_late(installment, today)
        last_payment = max((p.payment_date for p in credit.payments), default=None)
        rows.append(
            OverdueRow(
                client_id=credit.client_id,
                client_name=credit.client.full_name,
                client_credit_status=credit.client.credit_status,
                credit_id=credit.id,
                credit_code=credit.code,
                due_date=installment.due_date,
                days_late=days,
                overdue_balance=outstanding,
                late_interest=finance.late_interest(outstanding, days),
                credit_status=credit.status,
                last_payment_date=last_payment,
            )
        )

    rows.sort(key=lambda row: row.days_late, reverse=True)
    return OverdueResponse(
        blocked_clients=clients_repo.count_blocked(session),
        overdue_balance=money(sum((r.overdue_balance for r in rows), ZERO_MONEY)),
        overdue_installments=len(rows),
        rows=rows,
    )
