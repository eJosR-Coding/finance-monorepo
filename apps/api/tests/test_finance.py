"""Financial engine tests: rate conversion, French method and late interest.

Test names stay in Spanish on purpose - the pytest output goes straight into
the academic report (Anexo F), so the professor reads them as evidence.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.core.enums import GraceType, RateType
from app.core.errors import BusinessRuleError
from app.services import finance
from scripts.academic_cases import ACADEMIC_CASES, AcademicCase

START = date(2026, 9, 12)


def _schedule(case: AcademicCase) -> finance.Schedule:
    return finance.build_schedule(
        amount=case.amount,
        rate_type=case.rate_type,
        annual_rate=case.annual_rate,
        start_date=case.start_date,
        term_days=case.term_days,
        installments_count=case.installments_count,
        payment_frequency_days=case.payment_frequency_days,
    )


# ── Mandatory academic cases (Anexo C) ─────────────────────────────────────


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_caso_academico_reproduce_los_valores_esperados(case: AcademicCase) -> None:
    schedule = _schedule(case)

    assert schedule.periodic_rate == case.expected_periodic_rate
    assert schedule.periodic_rate_percent == case.expected_periodic_rate_percent
    assert schedule.installment_amount == case.expected_installment
    assert schedule.total_interest == case.expected_total_interest
    assert schedule.total_payment == case.expected_total_payment
    assert schedule.final_balance == case.expected_final_balance
    assert len(schedule.rows) == len(case.expected_rows)

    for row, expected in zip(schedule.rows, case.expected_rows, strict=True):
        assert row.installment_number == expected.installment_number
        assert row.opening_balance == expected.opening_balance
        assert row.interest_amount == expected.interest_amount
        assert row.amortization_amount == expected.amortization_amount
        assert row.installment_amount == expected.installment_amount
        assert row.closing_balance == expected.closing_balance


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_caso_academico_cuadra_capital_mas_intereses(case: AcademicCase) -> None:
    """Total payable == principal + total interest. No cents lost in the sauce."""
    schedule = _schedule(case)
    assert schedule.total_payment == schedule.amount + schedule.total_interest


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_caso_academico_amortizacion_suma_el_capital(case: AcademicCase) -> None:
    schedule = _schedule(case)
    amortized = sum(row.amortization_amount for row in schedule.rows)
    assert amortized == schedule.amount


# ── Rate conversion ────────────────────────────────────────────────────────


def test_tea_a_tasa_periodica_usa_base_360() -> None:
    """TEA 40 % over 7 days: (1 + 0.40)^(7/360) - 1 = 0.006563965."""
    assert finance.periodic_rate(RateType.TEA, Decimal("40.00"), 7) == Decimal("0.006563965")


def test_tna_es_proporcional_no_capitaliza() -> None:
    """TNA 36 % over 30 days: 0.36 * 30/360 = exactly 0.03."""
    assert finance.periodic_rate(RateType.TNA, Decimal("36.00"), 30) == Decimal("0.030000000")


def test_tasa_periodica_tiene_al_menos_7_decimales_en_porcentaje() -> None:
    percent = finance.periodic_rate(RateType.TEA, Decimal("40.00"), 7) * 100
    assert -percent.as_tuple().exponent >= 7


def test_tasa_anual_negativa_es_rechazada() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.periodic_rate(RateType.TEA, Decimal("-1.00"), 7)
    assert exc.value.code == "RATE_NEGATIVE"


def test_tcea_equivale_a_la_tea_cuando_no_hay_comisiones() -> None:
    schedule = finance.build_schedule(
        amount=Decimal("140.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
        start_date=START, term_days=14, installments_count=2, payment_frequency_days=7,
    )
    assert schedule.tcea == Decimal("40.00")


# ── Zero rate ──────────────────────────────────────────────────────────────


def test_tasa_cero_reparte_el_capital_en_partes_iguales() -> None:
    schedule = finance.build_schedule(
        amount=Decimal("150.00"), rate_type=RateType.TEA, annual_rate=Decimal("0.00"),
        start_date=START, term_days=14, installments_count=3, payment_frequency_days=4,
    )
    assert schedule.periodic_rate == Decimal("0.000000000")
    assert schedule.installment_amount == Decimal("50.00")
    assert schedule.total_interest == Decimal("0.00")
    assert schedule.total_payment == Decimal("150.00")
    assert all(row.interest_amount == Decimal("0.00") for row in schedule.rows)
    assert schedule.final_balance == Decimal("0.00")


# ── Final balance must be exactly zero ─────────────────────────────────────


@pytest.mark.parametrize("amount", ["1.00", "33.33", "99.99", "140.00", "200.00"])
@pytest.mark.parametrize("installments", [1, 2, 3, 7])
@pytest.mark.parametrize("annual_rate", ["0.00", "12.50", "40.00", "60.00", "180.00"])
def test_el_saldo_final_siempre_cierra_en_cero(
    amount: str, installments: int, annual_rate: str
) -> None:
    """The last installment absorbs the rounding residue, no matter the inputs."""
    schedule = finance.build_schedule(
        amount=Decimal(amount), rate_type=RateType.TEA, annual_rate=Decimal(annual_rate),
        start_date=START, term_days=14, installments_count=installments,
        payment_frequency_days=14 // installments,
    )
    assert schedule.final_balance == Decimal("0.00")
    assert sum(r.amortization_amount for r in schedule.rows) == Decimal(amount)
    assert schedule.total_payment == Decimal(amount) + schedule.total_interest


# ── Product limits ─────────────────────────────────────────────────────────


def test_monto_mayor_al_maximo_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("200.01"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=14, installments_count=2, payment_frequency_days=7,
        )
    assert exc.value.code == "AMOUNT_ABOVE_MAX"
    assert "200.00" in exc.value.message


def test_monto_cero_o_negativo_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("0.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=14, installments_count=1, payment_frequency_days=7,
        )
    assert exc.value.code == "AMOUNT_NOT_POSITIVE"


def test_plazo_mayor_al_maximo_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("100.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=15, installments_count=2, payment_frequency_days=7,
        )
    assert exc.value.code == "TERM_ABOVE_MAX"
    assert "14" in exc.value.message


def test_el_cronograma_no_puede_pasarse_del_plazo_pactado() -> None:
    """3 installments every 7 days = 21 days, but the term is 14."""
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("100.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=14, installments_count=3, payment_frequency_days=7,
        )
    assert exc.value.code == "SCHEDULE_EXCEEDS_TERM"


def test_numero_de_cuotas_invalido_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("100.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=14, installments_count=0, payment_frequency_days=7,
        )
    assert exc.value.code == "INSTALLMENTS_INVALID"


# ── Due dates ──────────────────────────────────────────────────────────────


def test_las_fechas_de_vencimiento_siguen_la_frecuencia() -> None:
    schedule = finance.build_schedule(
        amount=Decimal("140.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
        start_date=date(2026, 9, 12), term_days=14,
        installments_count=2, payment_frequency_days=7,
    )
    assert [row.due_date for row in schedule.rows] == [date(2026, 9, 19), date(2026, 9, 26)]


# ── Grace periods ──────────────────────────────────────────────────────────


def test_gracia_parcial_agrega_una_cuota_de_solo_interes() -> None:
    schedule = finance.build_schedule(
        amount=Decimal("140.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
        start_date=START, term_days=14, installments_count=1, payment_frequency_days=7,
        grace_type=GraceType.partial, grace_days=7,
    )
    grace_row = schedule.rows[0]
    assert grace_row.amortization_amount == Decimal("0.00")
    assert grace_row.opening_balance == grace_row.closing_balance == Decimal("140.00")
    assert grace_row.installment_amount == grace_row.interest_amount
    assert schedule.financed_principal == Decimal("140.00")
    assert schedule.final_balance == Decimal("0.00")


def test_gracia_total_capitaliza_el_interes_al_principal() -> None:
    schedule = finance.build_schedule(
        amount=Decimal("140.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
        start_date=START, term_days=14, installments_count=1, payment_frequency_days=7,
        grace_type=GraceType.total, grace_days=7,
    )
    assert schedule.financed_principal > schedule.amount
    assert schedule.rows[0].opening_balance == schedule.financed_principal
    assert schedule.final_balance == Decimal("0.00")


def test_gracia_incoherente_es_rechazada() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        finance.build_schedule(
            amount=Decimal("140.00"), rate_type=RateType.TEA, annual_rate=Decimal("40.00"),
            start_date=START, term_days=14, installments_count=2, payment_frequency_days=7,
            grace_type=GraceType.none, grace_days=3,
        )
    assert exc.value.code == "GRACE_INVALID"


# ── Late interest ──────────────────────────────────────────────────────────


def test_sin_dias_de_atraso_no_hay_mora() -> None:
    assert finance.late_interest(Decimal("70.69"), 0) == Decimal("0.00")
    assert finance.late_interest(Decimal("70.69"), -3) == Decimal("0.00")


def test_la_mora_crece_con_los_dias_de_atraso() -> None:
    uno = finance.late_interest(Decimal("100.00"), 1)
    cinco = finance.late_interest(Decimal("100.00"), 5)
    assert Decimal("0.00") < uno < cinco


def test_mora_de_un_mes_equivale_a_la_tem_configurada() -> None:
    """30 days late on S/ 100.00 at a 2 % monthly rate = S/ 2.00 flat."""
    assert finance.late_interest(Decimal("100.00"), 30) == Decimal("2.00")
