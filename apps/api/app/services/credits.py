"""Credit use cases: simulate, grant and query."""

from datetime import date

from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.enums import ClientCreditStatus, CreditStatus, InstallmentStatus
from app.core.errors import BusinessRuleError, NotFoundError
from app.models import Client, Credit, Installment
from app.repositories import clients as clients_repo
from app.repositories import credits as credits_repo
from app.schemas.credit import (
    CreditDetail,
    CreditListItem,
    CreditTerms,
    InstallmentRead,
    ScheduleRowRead,
    SimulationRequest,
    SimulationResponse,
)
from app.services import balances, delinquency, finance

BLOCKED_MESSAGE = (
    "Este cliente mantiene una deuda vencida y no puede recibir un nuevo credito."
)


# ══════════════════════════════════════════════════════════════════════════
# Simulation (persists absolutely nothing)
# ══════════════════════════════════════════════════════════════════════════


def simulate(payload: SimulationRequest) -> SimulationResponse:
    schedule = finance.build_schedule(
        amount=payload.amount,
        rate_type=payload.rate_type,
        annual_rate=payload.annual_rate,
        start_date=payload.start_date,
        term_days=payload.term_days,
        installments_count=payload.installments_count,
        payment_frequency_days=payload.payment_frequency_days,
        grace_type=payload.grace_type,
        grace_days=payload.grace_days,
    )
    return SimulationResponse(
        amount=schedule.amount,
        financed_principal=schedule.financed_principal,
        rate_type=schedule.rate_type,
        annual_rate=schedule.annual_rate,
        periodic_rate=schedule.periodic_rate,
        periodic_rate_percent=schedule.periodic_rate_percent,
        installment_amount=schedule.installment_amount,
        total_interest=schedule.total_interest,
        total_payment=schedule.total_payment,
        final_balance=schedule.final_balance,
        tcea=schedule.tcea,
        term_days=payload.term_days,
        installments_count=len(schedule.rows),
        payment_frequency_days=payload.payment_frequency_days,
        grace_type=payload.grace_type,
        grace_days=payload.grace_days,
        late_monthly_rate_percent=settings.late_monthly_rate * 100,
        schedule=[
            ScheduleRowRead(
                installment_number=row.installment_number,
                due_date=row.due_date,
                opening_balance=row.opening_balance,
                interest=row.interest_amount,
                amortization=row.amortization_amount,
                installment=row.installment_amount,
                closing_balance=row.closing_balance,
            )
            for row in schedule.rows
        ],
    )


# ══════════════════════════════════════════════════════════════════════════
# Granting
# ══════════════════════════════════════════════════════════════════════════


def assert_client_can_borrow(client: Client) -> None:
    """A blocked client, or one with overdue debt, gets no new credit. Period."""
    if client.credit_status == ClientCreditStatus.blocked:
        raise BusinessRuleError("CLIENT_BLOCKED", BLOCKED_MESSAGE, client_id=client.id)
    if delinquency.has_overdue_debt(client):
        raise BusinessRuleError(
            "CLIENT_HAS_OVERDUE_DEBT", BLOCKED_MESSAGE, client_id=client.id
        )


def create(session: Session, payload: CreditTerms, today: date | None = None) -> Credit:
    """Grant a credit. All or nothing: credit + installments in one transaction."""
    today = today or clock.today()
    try:
        # Refresh delinquency state BEFORE deciding, not after.
        delinquency.sync(session, today)

        client = clients_repo.get(session, payload.client_id)
        if client is None:
            raise NotFoundError("CLIENT_NOT_FOUND", "El cliente indicado no existe.")
        assert_client_can_borrow(client)

        schedule = finance.build_schedule(
            amount=payload.amount,
            rate_type=payload.rate_type,
            annual_rate=payload.annual_rate,
            start_date=payload.start_date,
            term_days=payload.term_days,
            installments_count=payload.installments_count,
            payment_frequency_days=payload.payment_frequency_days,
            grace_type=payload.grace_type,
            grace_days=payload.grace_days,
        )

        credit = Credit(
            client_id=client.id,
            amount=schedule.amount,
            start_date=payload.start_date,
            term_days=payload.term_days,
            rate_type=payload.rate_type,
            annual_rate=schedule.annual_rate,
            periodic_rate=schedule.periodic_rate,
            # Partial grace adds an interest-only row, so we store the real
            # number of installments, not the requested one.
            installments_count=len(schedule.rows),
            payment_frequency_days=payload.payment_frequency_days,
            grace_type=payload.grace_type,
            grace_days=payload.grace_days,
            total_interest=schedule.total_interest,
            total_payment=schedule.total_payment,
            outstanding_balance=schedule.total_payment,
            status=CreditStatus.active,
        )
        credit.installments = [
            Installment(
                installment_number=row.installment_number,
                due_date=row.due_date,
                opening_balance=row.opening_balance,
                interest_amount=row.interest_amount,
                amortization_amount=row.amortization_amount,
                installment_amount=row.installment_amount,
                closing_balance=row.closing_balance,
                status=InstallmentStatus.pending,
            )
            for row in schedule.rows
        ]
        credits_repo.add(session, credit)
        session.commit()
    except Exception:
        session.rollback()
        raise

    refreshed = credits_repo.get(session, credit.id)
    assert refreshed is not None
    return refreshed


# ══════════════════════════════════════════════════════════════════════════
# Queries
# ══════════════════════════════════════════════════════════════════════════


def _next_due_date(credit: Credit) -> date | None:
    pending = [i for i in credit.installments if not balances.is_settled(i)]
    return min((i.due_date for i in pending), default=None)


def to_list_item(credit: Credit) -> CreditListItem:
    return CreditListItem(
        **_credit_fields(credit),
        client_name=credit.client.full_name,
        next_due_date=_next_due_date(credit),
    )


def _credit_fields(credit: Credit) -> dict:
    return {
        "id": credit.id,
        "client_id": credit.client_id,
        "amount": credit.amount,
        "start_date": credit.start_date,
        "term_days": credit.term_days,
        "rate_type": credit.rate_type,
        "annual_rate": credit.annual_rate,
        "periodic_rate": credit.periodic_rate,
        "installments_count": credit.installments_count,
        "payment_frequency_days": credit.payment_frequency_days,
        "grace_type": credit.grace_type,
        "grace_days": credit.grace_days,
        "total_interest": credit.total_interest,
        "total_payment": credit.total_payment,
        "outstanding_balance": credit.outstanding_balance,
        "status": credit.status,
        "created_at": credit.created_at,
    }


def to_installment_read(installment: Installment, today: date) -> InstallmentRead:
    return InstallmentRead(
        id=installment.id,
        installment_number=installment.installment_number,
        due_date=installment.due_date,
        opening_balance=installment.opening_balance,
        interest_amount=installment.interest_amount,
        amortization_amount=installment.amortization_amount,
        installment_amount=installment.installment_amount,
        closing_balance=installment.closing_balance,
        status=installment.status,
        paid_amount=balances.paid_amount(installment),
        outstanding_amount=balances.outstanding_amount(installment),
        days_late=delinquency.days_late(installment, today),
    )


def get_detail(session: Session, credit_id: int, today: date | None = None) -> CreditDetail:
    today = today or clock.today()
    delinquency.sync(session, today)
    session.commit()

    credit = credits_repo.get(session, credit_id)
    if credit is None:
        raise NotFoundError("CREDIT_NOT_FOUND", "El credito indicado no existe.")

    # The "headline" installment is the French one: first row that amortizes.
    french_rows = [i for i in credit.installments if i.amortization_amount > 0]
    installment_amount = (
        french_rows[0].installment_amount
        if french_rows
        else credit.installments[0].installment_amount
    )

    return CreditDetail(
        **_credit_fields(credit),
        client_name=credit.client.full_name,
        client_dni=credit.client.dni,
        client_credit_status=credit.client.credit_status,
        next_due_date=_next_due_date(credit),
        installment_amount=installment_amount,
        tcea=finance.annualize(credit.periodic_rate, credit.payment_frequency_days),
        late_monthly_rate_percent=settings.late_monthly_rate * 100,
        installments=[to_installment_read(i, today) for i in credit.installments],
    )


def list_credits(
    session: Session,
    *,
    client_id: int | None = None,
    status: CreditStatus | None = None,
    today: date | None = None,
) -> list[CreditListItem]:
    today = today or clock.today()
    delinquency.sync(session, today)
    session.commit()
    rows = credits_repo.list_all(session, client_id=client_id, status=status)
    return [to_list_item(credit) for credit in rows]
