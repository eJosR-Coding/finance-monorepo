"""Delinquency: flags overdue installments/credits and blocks or frees clients.

Runs on reads (dashboard, lists, detail) and before granting a credit, so the
state the user sees always matches today's date. For a local academic app this
is simpler and lowkey more honest than a cron job.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import clock
from app.core.enums import ClientCreditStatus, CreditStatus, InstallmentStatus
from app.core.money import ZERO_MONEY
from app.models import Client, Credit, Installment
from app.services import balances


def days_late(installment: Installment, today: date) -> int:
    """Days late for an installment. 0 if it's current or already settled."""
    if balances.is_settled(installment):
        return 0
    return max((today - installment.due_date).days, 0)


def sync(session: Session, today: date | None = None) -> None:
    """Recompute installment, credit and client states. Does not commit."""
    today = today or clock.today()

    credits = list(
        session.scalars(
            select(Credit).options(
                selectinload(Credit.installments).selectinload(Installment.payments)
            )
        )
    )

    for credit in credits:
        has_overdue = False
        all_settled = True

        for installment in credit.installments:
            if balances.is_settled(installment):
                installment.status = InstallmentStatus.paid
                continue
            all_settled = False
            if installment.due_date < today:
                installment.status = InstallmentStatus.overdue
                has_overdue = True
            else:
                installment.status = InstallmentStatus.pending

        credit.outstanding_balance = balances.credit_outstanding(credit)
        if all_settled:
            credit.status = CreditStatus.paid
            credit.outstanding_balance = ZERO_MONEY
        elif has_overdue:
            credit.status = CreditStatus.overdue
        else:
            credit.status = CreditStatus.active

    # A client stays blocked while at least one credit is overdue.
    clients = list(session.scalars(select(Client).options(selectinload(Client.credits))))
    for client in clients:
        blocked = any(credit.status == CreditStatus.overdue for credit in client.credits)
        client.credit_status = (
            ClientCreditStatus.blocked if blocked else ClientCreditStatus.enabled
        )


def has_overdue_debt(client: Client) -> bool:
    return any(credit.status == CreditStatus.overdue for credit in client.credits)
