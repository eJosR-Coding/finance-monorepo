"""Payment use cases: preview an allocation and actually record it.

The waterfall is fixed by the assignment and non-negotiable:
    1. late interest (mora)
    2. compensatory interest
    3. principal
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.enums import PaymentMethod
from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.money import ZERO_MONEY, money
from app.models import Credit, Installment, Payment
from app.repositories import credits as credits_repo
from app.repositories import payments as payments_repo
from app.schemas.payment import (
    PaymentAllocation,
    PaymentCreate,
    PaymentListItem,
    PaymentPreview,
    PaymentRead,
    PaymentResult,
)
from app.services import balances, delinquency, finance


@dataclass
class _Slice:
    """One installment's share of the money received."""

    installment: Installment
    late_interest: Decimal
    interest: Decimal
    principal: Decimal

    @property
    def total(self) -> Decimal:
        return money(self.late_interest + self.interest + self.principal)


def _late_interest_due(installment: Installment, payment_date: date) -> Decimal:
    """Late interest still owed on an installment, net of what was already charged."""
    outstanding = balances.outstanding_amount(installment)
    days = delinquency.days_late(installment, payment_date)
    accrued = finance.late_interest(outstanding, days)
    already_charged = balances.late_interest_paid(installment)
    return max(money(accrued - already_charged), ZERO_MONEY)


def _recent_duplicate(credit: Credit, payload: PaymentCreate, amount: Decimal, when: date):
    """Find a payment batch identical to this one inside the resubmit window.

    A single register() can write several Payment rows (money cascading into
    later installments), so we compare the SUM of the rows written recently with
    the same date and method against the amount being requested now.

    It's a heuristic, not a cryptographic idempotency key: two genuinely
    different payments that land in the same window and happen to add up to the
    same figure would trip it. That's why `allow_duplicate` exists - the caller
    can insist, and nothing is silently lost either way.
    """
    cutoff = clock.now() - timedelta(seconds=settings.duplicate_window_seconds)
    recent = [
        payment
        for payment in credit.payments
        if payment.created_at >= cutoff
        and payment.payment_date == when
        and payment.payment_method == (payload.payment_method or PaymentMethod.cash)
    ]
    if not recent:
        return None
    if money(sum((p.amount_received for p in recent), ZERO_MONEY)) != amount:
        return None
    return max(recent, key=lambda p: p.created_at)


def _targets(credit: Credit, installment_id: int | None) -> list[Installment]:
    """Unsettled installments to collect against, oldest first.

    `installment_id` just picks where to start; anything before it is skipped
    (the UI defaults to the oldest pending one anyway).
    """
    pending = sorted(
        (i for i in credit.installments if not balances.is_settled(i)),
        key=lambda i: i.installment_number,
    )
    if installment_id is None:
        return pending
    start = next((i for i in pending if i.id == installment_id), None)
    if start is None:
        raise NotFoundError(
            "INSTALLMENT_NOT_FOUND", "La cuota indicada no existe o ya esta pagada."
        )
    return [i for i in pending if i.installment_number >= start.installment_number]


def _allocate(
    credit: Credit, amount: Decimal, payment_date: date, installment_id: int | None
) -> tuple[list[_Slice], Decimal]:
    """Split `amount` across installments. Returns the slices and what's left over."""
    remaining = money(amount)
    slices: list[_Slice] = []

    for installment in _targets(credit, installment_id):
        if remaining <= ZERO_MONEY:
            break

        late_due = _late_interest_due(installment, payment_date)
        pay_late = min(remaining, late_due)
        remaining = money(remaining - pay_late)

        interest_due = balances.interest_pending(installment)
        pay_interest = min(remaining, interest_due)
        remaining = money(remaining - pay_interest)

        principal_due = balances.principal_pending(installment)
        pay_principal = min(remaining, principal_due)
        remaining = money(remaining - pay_principal)

        current = _Slice(installment, pay_late, pay_interest, pay_principal)
        if current.total == ZERO_MONEY:
            # Nothing left to apply here; move on instead of writing a no-op row.
            continue
        slices.append(current)

    return slices, remaining


def _outcome(target_due: Decimal, applied: Decimal, unapplied: Decimal) -> str:
    if unapplied > ZERO_MONEY:
        return "surplus"
    if applied >= target_due:
        return "exact"
    return "partial"


def preview(
    session: Session, credit_id: int, payload: PaymentCreate, today: date | None = None
) -> PaymentPreview:
    """Dry run: show the split without writing anything."""
    today = today or clock.today()
    delinquency.sync(session, today)
    session.commit()

    credit = credits_repo.get(session, credit_id)
    if credit is None:
        raise NotFoundError("CREDIT_NOT_FOUND", "El credito indicado no existe.")

    payment_date = payload.payment_date or today
    targets = _targets(credit, payload.installment_id)
    if not targets:
        raise ConflictError("CREDIT_ALREADY_PAID", "Este credito ya esta cancelado.")

    first = targets[0]
    target_due = money(balances.outstanding_amount(first) + _late_interest_due(first, payment_date))

    slices, unapplied = _allocate(
        credit, payload.amount_received, payment_date, payload.installment_id
    )
    applied = money(sum((s.total for s in slices), ZERO_MONEY))
    principal_applied = money(sum((s.principal for s in slices), ZERO_MONEY))
    interest_applied = money(sum((s.interest for s in slices), ZERO_MONEY))
    late_applied = money(sum((s.late_interest for s in slices), ZERO_MONEY))

    return PaymentPreview(
        amount_received=money(payload.amount_received),
        due_amount=target_due,
        late_interest_amount=late_applied,
        compensatory_interest_amount=interest_applied,
        principal_amount=principal_applied,
        total_applied=applied,
        remaining_balance=money(credit.outstanding_balance - interest_applied - principal_applied),
        unapplied_amount=unapplied,
        outcome=_outcome(target_due, applied, unapplied),
        days_late=delinquency.days_late(first, payment_date),
        allocations=[_to_allocation(s) for s in slices],
    )


def _to_allocation(current: _Slice) -> PaymentAllocation:
    return PaymentAllocation(
        installment_id=current.installment.id,
        installment_number=current.installment.installment_number,
        late_interest_amount=current.late_interest,
        compensatory_interest_amount=current.interest,
        principal_amount=current.principal,
        total_applied=current.total,
        installment_status=current.installment.status,
    )


def register(
    session: Session, credit_id: int, payload: PaymentCreate, today: date | None = None
) -> PaymentResult:
    """Record a payment. Everything lands in one transaction or nothing does."""
    today = today or clock.today()
    try:
        delinquency.sync(session, today)

        credit = credits_repo.get(session, credit_id)
        if credit is None:
            raise NotFoundError("CREDIT_NOT_FOUND", "El credito indicado no existe.")

        amount = money(payload.amount_received)
        if amount <= ZERO_MONEY:
            raise BusinessRuleError("PAYMENT_NOT_POSITIVE", "El monto del pago debe ser mayor a 0.")

        payment_date = payload.payment_date or today
        if payment_date < credit.start_date:
            raise BusinessRuleError(
                "PAYMENT_BEFORE_CREDIT",
                "La fecha del pago no puede ser anterior a la fecha del credito.",
            )

        targets = _targets(credit, payload.installment_id)
        if not targets:
            raise ConflictError("CREDIT_ALREADY_PAID", "Este credito ya esta cancelado.")

        if not payload.allow_duplicate:
            twin = _recent_duplicate(credit, payload, amount, payment_date)
            if twin is not None:
                seconds = int((clock.now() - twin.created_at).total_seconds())
                raise ConflictError(
                    "DUPLICATE_PAYMENT",
                    f"Ya registraste un pago identico de S/ {amount:.2f} hace "
                    f"{seconds} segundos. Si el cliente pago dos veces, confirma "
                    f"para registrarlo igual.",
                    seconds_ago=seconds,
                    amount=str(amount),
                )

        slices, unapplied = _allocate(credit, amount, payment_date, payload.installment_id)
        if unapplied > ZERO_MONEY:
            # We don't hand back change: the bodega owner should charge the exact debt.
            acceptable = money(amount - unapplied)
            raise BusinessRuleError(
                "PAYMENT_EXCEEDS_DEBT",
                f"El monto excede la deuda pendiente. El maximo a cobrar es "
                f"S/ {acceptable:.2f}.",
                max_amount=str(acceptable),
            )

        created: list[Payment] = []
        balance = credit.outstanding_balance
        for current in slices:
            balance = money(balance - current.interest - current.principal)
            payment = Payment(
                credit_id=credit.id,
                installment_id=current.installment.id,
                payment_date=payment_date,
                amount_received=current.total,
                late_interest_amount=current.late_interest,
                compensatory_interest_amount=current.interest,
                principal_amount=current.principal,
                remaining_balance=balance,
                payment_method=payload.payment_method or PaymentMethod.cash,
                notes=payload.notes,
            )
            session.add(payment)
            current.installment.payments.append(payment)
            created.append(payment)

        session.flush()
        # Re-run the delinquency pass so installment/credit/client states settle.
        delinquency.sync(session, today)
        session.commit()
    except Exception:
        session.rollback()
        raise

    refreshed = credits_repo.get(session, credit_id)
    assert refreshed is not None

    return PaymentResult(
        credit_id=credit_id,
        payment_date=payment_date,
        amount_received=money(sum((p.amount_received for p in created), ZERO_MONEY)),
        late_interest_amount=money(sum((p.late_interest_amount for p in created), ZERO_MONEY)),
        compensatory_interest_amount=money(
            sum((p.compensatory_interest_amount for p in created), ZERO_MONEY)
        ),
        principal_amount=money(sum((p.principal_amount for p in created), ZERO_MONEY)),
        remaining_balance=refreshed.outstanding_balance,
        credit_status=refreshed.status,
        client_credit_status=refreshed.client.credit_status,
        allocations=[_to_allocation(s) for s in slices],
        payments=[PaymentRead.model_validate(p) for p in created],
    )


def list_all(session: Session) -> list[PaymentListItem]:
    """Every payment in the shop, newest first, with client and credit context."""
    return [
        PaymentListItem(
            **PaymentRead.model_validate(payment).model_dump(),
            credit_code=payment.credit.code,
            client_id=payment.credit.client_id,
            client_name=payment.credit.client.full_name,
        )
        for payment in payments_repo.list_all(session)
    ]


def list_for_credit(session: Session, credit_id: int) -> list[PaymentRead]:
    credit = credits_repo.get(session, credit_id)
    if credit is None:
        raise NotFoundError("CREDIT_NOT_FOUND", "El credito indicado no existe.")
    ordered = sorted(credit.payments, key=lambda p: (p.payment_date, p.id), reverse=True)
    return [PaymentRead.model_validate(p) for p in ordered]
