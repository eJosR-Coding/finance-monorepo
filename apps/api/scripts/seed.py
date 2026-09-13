"""Reproducible seed data for the demo.

Every credit and installment is produced by the real services, never by hand:
if a number shows up in the database it came out of the French engine. Hand
written rows would drift from the schedule and the demo would be cooked.

Dates are relative to today, so the seed always looks fresh:
    * 3 blocked clients with overdue installments
    * active credits due today and later this week
    * one fully paid credit
    * one client with no credit history at all

Run it with:  uv run python scripts/seed.py
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.core import clock  # noqa: E402
from app.core.enums import PaymentMethod, RateType  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, create_all, engine  # noqa: E402
from app.models import Client, Credit, User  # noqa: E402
from app.repositories import credits as credits_repo  # noqa: E402
from app.schemas.client import ClientCreate  # noqa: E402
from app.schemas.credit import CreditTerms  # noqa: E402
from app.schemas.payment import PaymentCreate  # noqa: E402
from app.services import balances, delinquency, finance  # noqa: E402  # noqa: E402
from app.services import clients as clients_service
from app.services import credits as credits_service  # noqa: E402
from app.services import payments as payments_service  # noqa: E402

ADMIN_NAME = "Carlos Mendoza"
ADMIN_EMAIL = "admin@prestameami.pe"
ADMIN_PASSWORD = "admin123"

TODAY = clock.today()


def reset_database() -> None:
    """Drop everything and rebuild. The seed is the whole truth, not a patch."""
    Base.metadata.drop_all(bind=engine)
    create_all()


def create_admin(session: Session) -> User:
    admin = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
    )
    session.add(admin)
    session.commit()
    return admin


def add_client(
    session: Session, dni: str, first: str, last: str, phone: str, address: str
) -> Client:
    return clients_service.create(
        session,
        ClientCreate(dni=dni, first_name=first, last_name=last, phone=phone, address=address),
    )


def grant(
    session: Session,
    client: Client,
    *,
    amount: str,
    annual_rate: str,
    starts_days_ago: int,
    term_days: int,
    installments: int,
    frequency_days: int,
) -> Credit:
    return credits_service.create(
        session,
        CreditTerms(
            client_id=client.id,
            amount=Decimal(amount),
            rate_type=RateType.TEA,
            annual_rate=Decimal(annual_rate),
            start_date=TODAY - timedelta(days=starts_days_ago),
            term_days=term_days,
            installments_count=installments,
            payment_frequency_days=frequency_days,
        ),
    )


def pay_installment(
    session: Session,
    credit_id: int,
    installment_number: int,
    *,
    on: date,
    method: PaymentMethod = PaymentMethod.cash,
    amount: str | None = None,
    notes: str | None = None,
) -> None:
    """Collect one installment. Without `amount` it pays exactly what's owed."""
    delinquency.sync(session, TODAY)
    session.commit()

    credit = credits_repo.get(session, credit_id)
    assert credit is not None
    installment = next(
        i for i in credit.installments if i.installment_number == installment_number
    )

    if amount is None:
        outstanding = balances.outstanding_amount(installment)
        late = finance.late_interest(outstanding, delinquency.days_late(installment, on))
        due = outstanding + late
    else:
        due = Decimal(amount)

    payments_service.register(
        session,
        credit_id,
        PaymentCreate(
            amount_received=due,
            payment_method=method,
            payment_date=on,
            installment_id=installment.id,
            notes=notes,
        ),
    )


def seed(session: Session) -> None:
    create_admin(session)

    # ── 1. Maria Torres: the demo's leading lady. Enabled, one live credit. ──
    maria = add_client(
        session, "71456238", "Maria", "Torres", "987 234 521", "Av. Los Jardines 245, Lima"
    )
    grant(
        session, maria, amount="140.00", annual_rate="40.00",
        starts_days_ago=2, term_days=14, installments=2, frequency_days=7,
    )

    # ── 2. Luis Herrera: paid up, clean record. ──────────────────────────────
    luis = add_client(
        session, "70128455", "Luis", "Herrera", "965 118 920", "Jr. Union 120, Lima"
    )
    luis_credit = grant(
        session, luis, amount="100.00", annual_rate="40.00",
        starts_days_ago=10, term_days=7, installments=1, frequency_days=7,
    )
    pay_installment(
        session, luis_credit.id, 1, on=TODAY - timedelta(days=3),
        method=PaymentMethod.yape, notes="Pago completo en la tienda.",
    )

    # ── 3. Andrea Flores: overdue, partially paid -> blocked. ────────────────
    andrea = add_client(
        session, "72412982", "Andrea", "Flores", "912 455 885", "Calle Los Olivos 88, Lima"
    )
    andrea_credit = grant(
        session, andrea, amount="120.00", annual_rate="40.00",
        starts_days_ago=20, term_days=14, installments=2, frequency_days=7,
    )
    pay_installment(
        session, andrea_credit.id, 1, on=TODAY - timedelta(days=13),
        amount="40.00", method=PaymentMethod.cash, notes="Abono parcial.",
    )

    # ── 4. Pedro Salazar: first installment paid, second overdue -> blocked. ─
    pedro = add_client(
        session, "68934521", "Pedro", "Salazar", "945 782 310", "Av. Grau 410, Lima"
    )
    pedro_credit = grant(
        session, pedro, amount="90.00", annual_rate="45.00",
        starts_days_ago=16, term_days=14, installments=2, frequency_days=7,
    )
    pay_installment(
        session, pedro_credit.id, 1, on=TODAY - timedelta(days=9), method=PaymentMethod.plin
    )

    # ── 5. Marcela Diaz: one day late -> blocked, fresh delinquency. ─────────
    marcela = add_client(
        session, "73102845", "Marcela", "Diaz", "978 441 209", "Psje. Santa Rosa 12, Lima"
    )
    grant(
        session, marcela, amount="60.00", annual_rate="35.00",
        starts_days_ago=8, term_days=7, installments=1, frequency_days=7,
    )

    # ── 6. Jorge Chavez: installment due TODAY, already collected today. ─────
    jorge = add_client(
        session, "74589120", "Jorge", "Chavez", "923 887 145", "Av. Brasil 1520, Lima"
    )
    jorge_credit = grant(
        session, jorge, amount="180.00", annual_rate="50.00",
        starts_days_ago=7, term_days=14, installments=2, frequency_days=7,
    )
    pay_installment(
        session, jorge_credit.id, 1, on=TODAY,
        method=PaymentMethod.transfer, notes="Cobro del dia.",
    )

    # ── 7. Rosa Quispe: registered, never borrowed. Empty-state material. ────
    add_client(
        session, "75210983", "Rosa", "Quispe", "956 330 471", "Av. Tupac Amaru 77, Lima"
    )

    delinquency.sync(session, TODAY)
    session.commit()


def report(session: Session) -> None:
    from app.services import dashboard as dashboard_service

    summary = dashboard_service.build(session, TODAY)
    print(f"  Fecha de referencia   : {TODAY.isoformat()}")
    print(f"  Administrador         : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Creditos activos      : {summary.active_credits}")
    print(f"  Saldo por cobrar      : S/ {summary.outstanding_total}")
    print(f"  Cobros de hoy         : S/ {summary.collected_today} ({summary.payments_today})")
    print(f"  Clientes bloqueados   : {summary.blocked_clients}")
    print(f"  Cuotas vencidas       : {summary.overdue_installments}")
    print(f"  Saldo vencido         : S/ {summary.overdue_balance}")


def main() -> None:
    print("Reiniciando la base de datos...")
    reset_database()
    with SessionLocal() as session:
        seed(session)
        print("Datos de ejemplo cargados.\n")
        report(session)


if __name__ == "__main__":
    main()
