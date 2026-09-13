"""Helpers de precision monetaria.

Regla del proyecto: plata con Decimal, nunca float. Se redondea SOLO al final,
cuando el numero ya va a guardarse o mostrarse.
"""

from decimal import Decimal, ROUND_HALF_UP

MONEY_EXPONENT = Decimal("0.01")  # 2 decimales para importes
RATE_EXPONENT = Decimal("0.0000001")  # 7 decimales para tasas

ZERO_MONEY = Decimal("0.00")
ZERO_RATE = Decimal("0.0000000")


def money(value: Decimal | int | str) -> Decimal:
    """Redondea un importe a 2 decimales (medio hacia arriba)."""
    return Decimal(value).quantize(MONEY_EXPONENT, rounding=ROUND_HALF_UP)


def rate(value: Decimal | int | str) -> Decimal:
    """Redondea una tasa a 7 decimales."""
    return Decimal(value).quantize(RATE_EXPONENT, rounding=ROUND_HALF_UP)


def percent_to_decimal(value: Decimal | int | str) -> Decimal:
    """40.00 (%) -> 0.40. Sin redondear: la division queda en precision plena."""
    return Decimal(value) / Decimal(100)


def decimal_to_percent(value: Decimal | int | str) -> Decimal:
    """0.0065644 -> 0.65644 (%)."""
    return Decimal(value) * Decimal(100)
