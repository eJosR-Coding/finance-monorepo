"""Motor financiero: conversion de tasas, metodo frances y mora.

Modulo puro: no sabe nada de la base de datos ni de FastAPI. Recibe numeros y
fechas, devuelve un cronograma. Es el unico lugar del proyecto donde se
calculan formulas financieras — el frontend nunca las repite.

Convenciones:
  * Anio financiero de 360 dias.
  * Tasas como fraccion decimal con 9 decimales (== 7 decimales en porcentaje).
  * Importes con Decimal de 2 decimales; se redondea al cierre de cada periodo,
    nunca antes.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, getcontext

from app.core.config import settings
from app.core.enums import GraceType, RateType
from app.core.errors import BusinessRuleError
from app.core.money import ZERO_MONEY, money, percent_to_decimal, rate, rate_percent

# Margen de sobra para las potencias fraccionarias; el redondeo se hace explicito.
getcontext().prec = 28

ONE = Decimal(1)


# ══════════════════════════════════════════════════════════════════════════
# Tasas
# ══════════════════════════════════════════════════════════════════════════


def periodic_rate(rate_type: RateType, annual_rate_percent: Decimal, days: int) -> Decimal:
    """Tasa efectiva para un periodo de `days` dias, a partir de la tasa anual.

    TEA (efectiva):  i_d = (1 + TEA)^(d/360) - 1
    TNA (nominal):   i_d = TNA * d/360        (proporcional, sin capitalizar)

    `annual_rate_percent` viene en porcentaje (40.00 == 40 %).
    """
    if days <= 0:
        raise BusinessRuleError(
            "FREQUENCY_INVALID", "La frecuencia de pago debe ser de al menos 1 dia."
        )
    if annual_rate_percent < 0:
        raise BusinessRuleError("RATE_NEGATIVE", "La tasa anual no puede ser negativa.")

    annual = percent_to_decimal(annual_rate_percent)
    if annual == 0:
        return rate(0)

    factor = Decimal(days) / Decimal(settings.days_per_year)
    if rate_type is RateType.TEA:
        # Efectiva: capitaliza dentro del anio.
        return rate((ONE + annual) ** factor - ONE)
    # Nominal: proporcional, no capitaliza.
    return rate(annual * factor)


def annualize(periodic: Decimal, days: int) -> Decimal:
    """Lleva una tasa periodica a su equivalente anual efectiva, en %.

    Sin comisiones ni seguros, esta es la TCEA del credito.
    """
    if periodic == 0:
        return Decimal("0.00")
    periods_per_year = Decimal(settings.days_per_year) / Decimal(days)
    annual = (ONE + periodic) ** periods_per_year - ONE
    return (annual * 100).quantize(Decimal("0.01"))


def late_interest(overdue_amount: Decimal, days_late: int) -> Decimal:
    """Interes moratorio sobre el saldo exigible vencido.

    Se aplica la tasa moratoria configurada (TEM) prorrateada a los dias de
    atraso:  i = (1 + TEM)^(dias/30) - 1
    """
    if days_late <= 0 or overdue_amount <= 0:
        return ZERO_MONEY
    exponent = Decimal(days_late) / Decimal(settings.late_rate_base_days)
    factor = (ONE + settings.late_monthly_rate) ** exponent - ONE
    return money(overdue_amount * factor)


# ══════════════════════════════════════════════════════════════════════════
# Cronograma (metodo frances)
# ══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ScheduleRow:
    installment_number: int
    due_date: date
    opening_balance: Decimal
    interest_amount: Decimal
    amortization_amount: Decimal
    installment_amount: Decimal
    closing_balance: Decimal


@dataclass(frozen=True)
class Schedule:
    amount: Decimal  # capital solicitado
    financed_principal: Decimal  # capital sobre el que se arma el frances
    rate_type: RateType
    annual_rate: Decimal  # en %, tal como la ingreso el usuario
    periodic_rate: Decimal  # fraccion decimal, 9 dp
    periodic_rate_percent: Decimal  # el mismo valor en %, 7 dp
    installment_amount: Decimal  # cuota constante del tramo frances
    total_interest: Decimal
    total_payment: Decimal
    tcea: Decimal  # % anual
    rows: tuple[ScheduleRow, ...]

    @property
    def final_balance(self) -> Decimal:
        return self.rows[-1].closing_balance if self.rows else ZERO_MONEY


def french_installment(principal: Decimal, periodic: Decimal, periods: int) -> Decimal:
    """Cuota constante del metodo frances, sin redondear.

        C = P * [ i (1+i)^n ] / [ (1+i)^n - 1 ]

    Con i = 0 degenera en C = P / n.
    """
    if periods <= 0:
        raise BusinessRuleError(
            "INSTALLMENTS_INVALID", "El numero de cuotas debe ser de al menos 1."
        )
    if periodic == 0:
        return principal / Decimal(periods)
    growth = (ONE + periodic) ** periods
    return principal * (periodic * growth) / (growth - ONE)


def build_schedule(
    *,
    amount: Decimal,
    rate_type: RateType,
    annual_rate: Decimal,
    start_date: date,
    term_days: int,
    installments_count: int,
    payment_frequency_days: int,
    grace_type: GraceType = GraceType.none,
    grace_days: int = 0,
) -> Schedule:
    """Arma el cronograma completo de un credito.

    Periodo de gracia:
      * `none`    — las cuotas arrancan en start_date + frecuencia.
      * `partial` — se cobra solo el interes del tramo de gracia como una cuota
        extra (la N.deg 1); el capital no se toca y el frances arranca despues.
      * `total`   — el interes del tramo de gracia se capitaliza al principal y
        el frances corre sobre ese capital mayor, con las fechas corridas.
    """
    validate_terms(
        amount=amount,
        term_days=term_days,
        installments_count=installments_count,
        payment_frequency_days=payment_frequency_days,
        annual_rate=annual_rate,
        grace_type=grace_type,
        grace_days=grace_days,
    )

    effective_grace_days = grace_days if grace_type is not GraceType.none else 0
    periodic = periodic_rate(rate_type, annual_rate, payment_frequency_days)

    rows: list[ScheduleRow] = []
    number = 0
    principal = amount
    first_due = start_date + timedelta(days=effective_grace_days)

    if effective_grace_days > 0:
        grace_rate = periodic_rate(rate_type, annual_rate, effective_grace_days)
        grace_interest = money(amount * grace_rate)
        if grace_type is GraceType.partial:
            # Cuota de solo interes: el saldo no se mueve.
            number += 1
            rows.append(
                ScheduleRow(
                    installment_number=number,
                    due_date=first_due,
                    opening_balance=amount,
                    interest_amount=grace_interest,
                    amortization_amount=ZERO_MONEY,
                    installment_amount=grace_interest,
                    closing_balance=amount,
                )
            )
        else:  # GraceType.total — el interes se capitaliza
            principal = money(amount + grace_interest)

    # Tramo frances.
    exact_installment = french_installment(principal, periodic, installments_count)
    constant_installment = money(exact_installment)

    balance = principal
    for period in range(1, installments_count + 1):
        number += 1
        due_date = first_due + timedelta(days=payment_frequency_days * period)
        interest = money(balance * periodic)
        is_last = period == installments_count
        if is_last:
            # La ultima cuota absorbe el residuo del redondeo: el saldo cierra en 0.00.
            amortization = balance
            installment = money(interest + amortization)
        else:
            amortization = money(constant_installment - interest)
            installment = constant_installment
            if amortization <= 0:
                raise BusinessRuleError(
                    "INSTALLMENT_BELOW_INTEREST",
                    "La cuota calculada no alcanza a cubrir el interes del periodo. "
                    "Revisa la tasa o el numero de cuotas.",
                )
        closing = money(balance - amortization)
        rows.append(
            ScheduleRow(
                installment_number=number,
                due_date=due_date,
                opening_balance=balance,
                interest_amount=interest,
                amortization_amount=amortization,
                installment_amount=installment,
                closing_balance=closing,
            )
        )
        balance = closing

    total_interest = money(sum((row.interest_amount for row in rows), ZERO_MONEY))
    total_payment = money(sum((row.installment_amount for row in rows), ZERO_MONEY))

    return Schedule(
        amount=money(amount),
        financed_principal=money(principal),
        rate_type=rate_type,
        annual_rate=Decimal(annual_rate).quantize(Decimal("0.01")),
        periodic_rate=periodic,
        periodic_rate_percent=rate_percent(periodic),
        installment_amount=constant_installment,
        total_interest=total_interest,
        total_payment=total_payment,
        tcea=annualize(periodic, payment_frequency_days),
        rows=tuple(rows),
    )


# ══════════════════════════════════════════════════════════════════════════
# Validaciones de condiciones
# ══════════════════════════════════════════════════════════════════════════


def validate_terms(
    *,
    amount: Decimal,
    term_days: int,
    installments_count: int,
    payment_frequency_days: int,
    annual_rate: Decimal,
    grace_type: GraceType = GraceType.none,
    grace_days: int = 0,
) -> None:
    """Aplica los limites del producto. Lanza BusinessRuleError con mensaje listo."""
    symbol = settings.currency_symbol

    if amount <= 0:
        raise BusinessRuleError("AMOUNT_NOT_POSITIVE", "El monto debe ser mayor a 0.")
    if amount > settings.max_credit_amount:
        raise BusinessRuleError(
            "AMOUNT_ABOVE_MAX",
            f"El monto maximo permitido es {symbol} {settings.max_credit_amount:.2f}.",
            max_amount=str(settings.max_credit_amount),
        )
    if term_days < settings.min_term_days:
        raise BusinessRuleError(
            "TERM_TOO_SHORT", f"El plazo minimo permitido es {settings.min_term_days} dia."
        )
    if term_days > settings.max_term_days:
        raise BusinessRuleError(
            "TERM_ABOVE_MAX",
            f"El plazo maximo permitido es {settings.max_term_days} dias.",
            max_term_days=settings.max_term_days,
        )
    if installments_count < 1:
        raise BusinessRuleError(
            "INSTALLMENTS_INVALID", "El numero de cuotas debe ser de al menos 1."
        )
    if payment_frequency_days < 1:
        raise BusinessRuleError(
            "FREQUENCY_INVALID", "La frecuencia de pago debe ser de al menos 1 dia."
        )
    if annual_rate < 0:
        raise BusinessRuleError("RATE_NEGATIVE", "La tasa anual no puede ser negativa.")
    if grace_days < 0:
        raise BusinessRuleError("GRACE_INVALID", "Los dias de gracia no pueden ser negativos.")
    if grace_type is GraceType.none and grace_days > 0:
        raise BusinessRuleError(
            "GRACE_INVALID", "Indicaste dias de gracia pero el tipo de gracia es 'sin gracia'."
        )
    if grace_type is not GraceType.none and grace_days < 1:
        raise BusinessRuleError(
            "GRACE_INVALID", "El periodo de gracia debe tener al menos 1 dia."
        )

    effective_grace = grace_days if grace_type is not GraceType.none else 0
    last_day = effective_grace + installments_count * payment_frequency_days
    if last_day > term_days:
        raise BusinessRuleError(
            "SCHEDULE_EXCEEDS_TERM",
            f"El cronograma termina en {last_day} dias y el plazo pactado es de "
            f"{term_days} dias. Ajusta el numero de cuotas o la frecuencia.",
            last_day=last_day,
            term_days=term_days,
        )
