"""Client use cases: register, search, update and build the detail view."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import clock
from app.core.enums import ClientCreditStatus, CreditStatus
from app.core.errors import ConflictError, NotFoundError
from app.core.money import ZERO_MONEY, money
from app.models import Client
from app.repositories import clients as clients_repo
from app.repositories import payments as payments_repo
from app.schemas.client import (
    ActivityItem,
    ClientCreate,
    ClientListItem,
    ClientUpdate,
)
from app.services import balances, delinquency
from app.services import credits as credits_service


def _outstanding(client: Client) -> Decimal:
    """What this client still owes across every open credit."""
    return money(
        sum(
            (
                balances.credit_outstanding(c)
                for c in client.credits
                if c.status != CreditStatus.paid
            ),
            ZERO_MONEY,
        )
    )


def _active_credits(client: Client) -> int:
    return sum(1 for c in client.credits if c.status != CreditStatus.paid)


def _last_movement(client: Client) -> datetime | None:
    """Most recent thing that happened to this client: a credit or a payment."""
    stamps = [client.created_at]
    for credit in client.credits:
        stamps.append(credit.created_at)
        stamps.extend(p.created_at for p in credit.payments)
    return max(stamps, default=None)


def to_list_item(client: Client) -> ClientListItem:
    return ClientListItem(
        id=client.id,
        dni=client.dni,
        first_name=client.first_name,
        last_name=client.last_name,
        phone=client.phone,
        address=client.address,
        credit_status=client.credit_status,
        created_at=client.created_at,
        updated_at=client.updated_at,
        active_credits=_active_credits(client),
        outstanding_balance=_outstanding(client),
        last_movement_at=_last_movement(client),
    )


def list_clients(
    session: Session,
    *,
    search: str | None = None,
    status: ClientCreditStatus | None = None,
    sort: str = "recent",
    today: date | None = None,
) -> list[ClientListItem]:
    delinquency.sync(session, today or clock.today())
    session.commit()

    items = [to_list_item(c) for c in clients_repo.list_all(session, search=search, status=status)]
    if sort == "debt":
        # Sorting in Python on purpose: amounts live as TEXT in SQLite, so an
        # ORDER BY would compare them as strings and that goes badly.
        items.sort(key=lambda item: item.outstanding_balance, reverse=True)
    return items


def get_client(session: Session, client_id: int, today: date | None = None) -> Client:
    delinquency.sync(session, today or clock.today())
    session.commit()
    client = clients_repo.get_with_credits(session, client_id)
    if client is None:
        raise NotFoundError("CLIENT_NOT_FOUND", "El cliente indicado no existe.")
    return client


def create(session: Session, payload: ClientCreate) -> Client:
    try:
        if clients_repo.get_by_dni(session, payload.dni) is not None:
            raise ConflictError(
                "DNI_ALREADY_EXISTS", f"Ya existe un cliente registrado con el DNI {payload.dni}."
            )
        client = Client(
            dni=payload.dni,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            address=payload.address,
            credit_status=ClientCreditStatus.enabled,
        )
        clients_repo.add(session, client)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return client


def update(session: Session, client_id: int, payload: ClientUpdate) -> Client:
    try:
        client = clients_repo.get_with_credits(session, client_id)
        if client is None:
            raise NotFoundError("CLIENT_NOT_FOUND", "El cliente indicado no existe.")

        data = payload.model_dump(exclude_unset=True)
        if data.get("credit_status") == ClientCreditStatus.enabled and delinquency.has_overdue_debt(
            client
        ):
            # Can't hand-wave a blocked client back to enabled while they're overdue.
            raise ConflictError(
                "CLIENT_HAS_OVERDUE_DEBT",
                "No se puede habilitar al cliente mientras mantenga una deuda vencida.",
            )
        for field, value in data.items():
            setattr(client, field, value)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return client


def build_activity(session: Session, client: Client) -> list[ActivityItem]:
    """Timeline for the client detail screen. Derived, never stored.

    Sorted by the underlying timestamp, not by `date`: a client registered,
    given credit and paid on the same day would otherwise come out shuffled.
    """
    entries: list[tuple[datetime, ActivityItem]] = [
        (
            client.created_at,
            ActivityItem(
                date=client.created_at.date(),
                type="client_created",
                title="Cliente registrado",
            ),
        )
    ]
    for credit in client.credits:
        entries.append(
            (
                credit.created_at,
                ActivityItem(
                    date=credit.created_at.date(),
                    type="credit_created",
                    title="Credito creado",
                    amount=credit.amount,
                    credit_id=credit.id,
                ),
            )
        )
    for payment in payments_repo.list_by_client(session, client.id):
        entries.append(
            (
                payment.created_at,
                ActivityItem(
                    date=payment.payment_date,
                    type="payment_registered",
                    title="Pago registrado",
                    amount=payment.amount_received,
                    credit_id=payment.credit_id,
                ),
            )
        )
    entries.sort(key=lambda entry: entry[0], reverse=True)
    return [item for _, item in entries]


def total_paid(session: Session, client_id: int) -> Decimal:
    payments = payments_repo.list_by_client(session, client_id)
    return money(sum((p.amount_received for p in payments), ZERO_MONEY))


def last_payment_date(session: Session, client_id: int) -> date | None:
    payments = payments_repo.list_by_client(session, client_id)
    return max((p.payment_date for p in payments), default=None)


def list_credit_items(session: Session, client_id: int) -> list:
    return credits_service.list_credits(session, client_id=client_id)
