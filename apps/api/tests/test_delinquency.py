"""Delinquency sync tested at the service level, on a long-lived session.

The API tests use one session per request, which hides identity-map staleness.
The seed script does everything in a single session, so these tests guard that
path: `sync` has to persist credit and client state no matter how much history
the session is already carrying.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ClientCreditStatus, CreditStatus, InstallmentStatus, RateType
from app.models import Client, Credit
from app.schemas.client import ClientCreate
from app.schemas.credit import CreditTerms
from app.schemas.payment import PaymentCreate
from app.services import clients as clients_service
from app.services import credits as credits_service
from app.services import delinquency
from app.services import payments as payments_service

TODAY = date(2026, 9, 12)


def _client(session: Session, dni: str = "71456238") -> Client:
    return clients_service.create(
        session,
        ClientCreate(
            dni=dni,
            first_name="Maria",
            last_name="Torres",
            phone="987 234 521",
            address="Av. Los Jardines 245, Lima",
        ),
    )


def _credit(session: Session, client: Client, *, starts_days_ago: int, amount: str) -> Credit:
    return credits_service.create(
        session,
        CreditTerms(
            client_id=client.id,
            amount=Decimal(amount),
            rate_type=RateType.TEA,
            annual_rate=Decimal("40.00"),
            start_date=TODAY - timedelta(days=starts_days_ago),
            term_days=14,
            installments_count=2,
            payment_frequency_days=7,
        ),
        today=TODAY,
    )


def test_sync_persiste_el_estado_en_la_misma_sesion(session: Session) -> None:
    """Regresion: los cambios de credito y cliente deben llegar a la base."""
    client = _client(session)
    credit = _credit(session, client, starts_days_ago=20, amount="120.00")

    delinquency.sync(session, TODAY)
    session.commit()

    # Read straight from the database, bypassing the ORM identity map.
    row = session.execute(
        select(Credit.status, Credit.outstanding_balance).where(Credit.id == credit.id)
    ).one()
    assert row.status == CreditStatus.overdue

    status = session.execute(
        select(Client.credit_status).where(Client.id == client.id)
    ).scalar_one()
    assert status == ClientCreditStatus.blocked


def test_credito_al_dia_no_bloquea_al_cliente(session: Session) -> None:
    client = _client(session)
    credit = _credit(session, client, starts_days_ago=0, amount="140.00")

    delinquency.sync(session, TODAY)
    session.commit()

    assert credit.status == CreditStatus.active
    assert client.credit_status == ClientCreditStatus.enabled
    assert all(i.status == InstallmentStatus.pending for i in credit.installments)


def test_cancelar_todo_marca_el_credito_pagado_y_libera_al_cliente(session: Session) -> None:
    client = _client(session)
    credit = _credit(session, client, starts_days_ago=20, amount="120.00")

    delinquency.sync(session, TODAY)
    session.commit()
    assert client.credit_status == ClientCreditStatus.blocked

    # Pay everything owed today, late interest included.
    preview = payments_service.preview(
        session, credit.id, PaymentCreate(amount_received=Decimal("500.00")), today=TODAY
    )
    payments_service.register(
        session,
        credit.id,
        PaymentCreate(amount_received=preview.total_applied, payment_date=TODAY),
        today=TODAY,
    )

    delinquency.sync(session, TODAY)
    session.commit()

    assert credit.status == CreditStatus.paid
    assert credit.outstanding_balance == Decimal("0.00")
    assert client.credit_status == ClientCreditStatus.enabled


def test_un_cliente_bloqueado_no_recibe_otro_credito(session: Session) -> None:
    from app.core.errors import BusinessRuleError

    client = _client(session)
    _credit(session, client, starts_days_ago=20, amount="120.00")

    try:
        _credit(session, client, starts_days_ago=0, amount="50.00")
    except BusinessRuleError as error:
        assert error.code in {"CLIENT_BLOCKED", "CLIENT_HAS_OVERDUE_DEBT"}
        assert "deuda vencida" in error.message
    else:  # pragma: no cover
        raise AssertionError("se otorgo un credito a un cliente bloqueado")
