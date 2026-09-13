"""Client data access."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ClientCreditStatus
from app.models import Client, Credit


def get(session: Session, client_id: int) -> Client | None:
    return session.get(Client, client_id)


def get_with_credits(session: Session, client_id: int) -> Client | None:
    return session.scalar(
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.credits).selectinload(Credit.installments))
    )


def get_by_dni(session: Session, dni: str) -> Client | None:
    return session.scalar(select(Client).where(Client.dni == dni))


def list_all(
    session: Session,
    *,
    search: str | None = None,
    status: ClientCreditStatus | None = None,
) -> list[Client]:
    """List clients with credits eager-loaded - a bodega's dataset is tiny."""
    statement = select(Client).options(
        selectinload(Client.credits).selectinload(Credit.installments)
    )
    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Client.first_name).like(pattern),
                func.lower(Client.last_name).like(pattern),
                func.lower(Client.first_name + " " + Client.last_name).like(pattern),
                Client.dni.like(pattern),
            )
        )
    if status is not None:
        statement = statement.where(Client.credit_status == status)
    return list(session.scalars(statement.order_by(Client.id.desc())))


def count_blocked(session: Session) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(Client)
            .where(Client.credit_status == ClientCreditStatus.blocked)
        )
        or 0
    )


def add(session: Session, client: Client) -> Client:
    session.add(client)
    session.flush()
    return client
