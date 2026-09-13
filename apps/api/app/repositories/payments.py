"""Payment data access."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Credit, Payment


def list_all(session: Session) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment)
            .options(selectinload(Payment.credit).selectinload(Credit.client))
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )
    )


def list_by_credit(session: Session, credit_id: int) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment)
            .where(Payment.credit_id == credit_id)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )
    )


def list_by_client(session: Session, client_id: int) -> list[Payment]:
    return list(
        session.scalars(
            select(Payment)
            .join(Credit, Payment.credit_id == Credit.id)
            .where(Credit.client_id == client_id)
            .options(selectinload(Payment.credit))
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )
    )


def list_by_date(session: Session, day: date) -> list[Payment]:
    return list(session.scalars(select(Payment).where(Payment.payment_date == day)))


def count_all(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Payment)) or 0
