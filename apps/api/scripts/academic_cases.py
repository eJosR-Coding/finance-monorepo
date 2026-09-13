"""Academic test cases (Anexo C and Anexo F).

Single source of truth: the tests assert the engine reproduces these numbers and
the docs generator builds its tables from here. Change a value once, it changes
everywhere - no duplicated tables drifting apart.

The `expected_*` values were worked out by hand with the formulas from the
assignment (TEA conversion on a 360 base + French method) and then checked
against the implementation.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.core.enums import RateType


@dataclass(frozen=True)
class ExpectedRow:
    installment_number: int
    opening_balance: Decimal
    interest_amount: Decimal
    amortization_amount: Decimal
    installment_amount: Decimal
    closing_balance: Decimal


@dataclass(frozen=True)
class AcademicCase:
    key: str
    title: str
    amount: Decimal
    rate_type: RateType
    annual_rate: Decimal
    start_date: date
    term_days: int
    installments_count: int
    payment_frequency_days: int

    expected_periodic_rate: Decimal
    expected_periodic_rate_percent: Decimal
    expected_installment: Decimal
    expected_total_interest: Decimal
    expected_total_payment: Decimal
    expected_final_balance: Decimal
    expected_rows: tuple[ExpectedRow, ...]


CASE_1 = AcademicCase(
    key="caso-1",
    title="Caso 1 — S/ 200.00, TEA 60 %, 14 dias, 2 cuotas cada 7 dias",
    amount=Decimal("200.00"),
    rate_type=RateType.TEA,
    annual_rate=Decimal("60.00"),
    start_date=date(2026, 9, 12),
    term_days=14,
    installments_count=2,
    payment_frequency_days=7,
    expected_periodic_rate=Decimal("0.009180847"),
    expected_periodic_rate_percent=Decimal("0.9180847"),
    expected_installment=Decimal("101.38"),
    expected_total_interest=Decimal("2.76"),
    expected_total_payment=Decimal("202.76"),
    expected_final_balance=Decimal("0.00"),
    expected_rows=(
        ExpectedRow(1, Decimal("200.00"), Decimal("1.84"), Decimal("99.54"),
                    Decimal("101.38"), Decimal("100.46")),
        ExpectedRow(2, Decimal("100.46"), Decimal("0.92"), Decimal("100.46"),
                    Decimal("101.38"), Decimal("0.00")),
    ),
)

CASE_2 = AcademicCase(
    key="caso-2",
    title="Caso 2 — S/ 120.00, TEA 40 %, 14 dias, 2 cuotas cada 7 dias",
    amount=Decimal("120.00"),
    rate_type=RateType.TEA,
    annual_rate=Decimal("40.00"),
    start_date=date(2026, 9, 12),
    term_days=14,
    installments_count=2,
    payment_frequency_days=7,
    expected_periodic_rate=Decimal("0.006563965"),
    expected_periodic_rate_percent=Decimal("0.6563965"),
    expected_installment=Decimal("60.59"),
    expected_total_interest=Decimal("1.19"),
    expected_total_payment=Decimal("121.19"),
    expected_final_balance=Decimal("0.00"),
    expected_rows=(
        ExpectedRow(1, Decimal("120.00"), Decimal("0.79"), Decimal("59.80"),
                    Decimal("60.59"), Decimal("60.20")),
        # Last installment eats the rounding residue: 60.60, not 60.59.
        ExpectedRow(2, Decimal("60.20"), Decimal("0.40"), Decimal("60.20"),
                    Decimal("60.60"), Decimal("0.00")),
    ),
)

ACADEMIC_CASES: tuple[AcademicCase, ...] = (CASE_1, CASE_2)
