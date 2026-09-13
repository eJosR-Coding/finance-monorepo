"""Credit and installment data access."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import CreditStatus, InstallmentStatus
from app.models import Credit, Installment


def _loaded():
    return (
        selectinload(Credit.installments).selectinload(Installment.payments),
        selectinload(Credit.client),
    )


def get(session: Session, credit_id: int) -> Credit | None:
    return session.scalar(select(Credit).where(Credit.id == credit_id).options(*_loaded()))


def list_all(
    session: Session,
    *,
    client_id: int | None = None,
    status: CreditStatus | None = None,
) -> list[Credit]:
    statement = select(Credit).options(*_loaded())
    if client_id is not None:
        statement = statement.where(Credit.client_id == client_id)
    if status is not None:
        statement = statement.where(Credit.status == status)
    return list(session.scalars(statement.order_by(Credit.id.desc())))


def list_open(session: Session) -> list[Credit]:
    """Credits that still owe money (active or overdue)."""
    return list(
        session.scalars(
            select(Credit)
            .where(Credit.status != CreditStatus.paid)
            .options(*_loaded())
            .order_by(Credit.id.desc())
        )
    )


def list_pending_installments(session: Session, *, until: date | None = None) -> list[Installment]:
    """Unsettled installments, nearest due date first."""
    statement = (
        select(Installment)
        .where(Installment.status != InstallmentStatus.paid)
        .options(selectinload(Installment.credit).selectinload(Credit.client))
        .order_by(Installment.due_date, Installment.id)
    )
    if until is not None:
        statement = statement.where(Installment.due_date <= until)
    return list(session.scalars(statement))


def get_installment(session: Session, installment_id: int) -> Installment | None:
    return session.get(Installment, installment_id)


def add(session: Session, credit: Credit) -> Credit:
    session.add(credit)
    session.flush()
    return credit
