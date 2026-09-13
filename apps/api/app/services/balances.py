"""Balances derived from installments and credits.

There is deliberately no "paid" column in the ERD: how much an installment has
received is deduced by summing its payments. These helpers are the single place
that math happens, so nobody reinvents it slightly differently elsewhere.
"""

from decimal import Decimal

from app.core.money import ZERO_MONEY, money
from app.models import Credit, Installment


def interest_paid(installment: Installment) -> Decimal:
    """Compensatory interest already collected on this installment."""
    return money(
        sum((p.compensatory_interest_amount for p in installment.payments), ZERO_MONEY)
    )


def principal_paid(installment: Installment) -> Decimal:
    """Principal already amortized on this installment."""
    return money(sum((p.principal_amount for p in installment.payments), ZERO_MONEY))


def late_interest_paid(installment: Installment) -> Decimal:
    """Late interest already collected on this installment."""
    return money(sum((p.late_interest_amount for p in installment.payments), ZERO_MONEY))


def paid_amount(installment: Installment) -> Decimal:
    """What was applied to the installment itself (late fees are a separate charge)."""
    return money(interest_paid(installment) + principal_paid(installment))


def outstanding_amount(installment: Installment) -> Decimal:
    """What is still owed on this installment."""
    return max(money(installment.installment_amount - paid_amount(installment)), ZERO_MONEY)


def interest_pending(installment: Installment) -> Decimal:
    return max(money(installment.interest_amount - interest_paid(installment)), ZERO_MONEY)


def principal_pending(installment: Installment) -> Decimal:
    return max(money(installment.amortization_amount - principal_paid(installment)), ZERO_MONEY)


def is_settled(installment: Installment) -> bool:
    return outstanding_amount(installment) == ZERO_MONEY


def credit_outstanding(credit: Credit) -> Decimal:
    """Credit outstanding: total payable minus whatever was applied to installments.

    Late interest stays out of it: it's an extra charge, it neither shrinks nor
    grows the agreed schedule balance.
    """
    return max(
        money(
            credit.total_payment
            - sum((paid_amount(i) for i in credit.installments), ZERO_MONEY)
        ),
        ZERO_MONEY,
    )
