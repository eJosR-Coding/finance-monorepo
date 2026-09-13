"""Helpers de precision monetaria.

Regla del proyecto: plata con Decimal, nunca float. Se redondea SOLO al final,
cuando el numero ya va a guardarse o mostrarse.
"""

from decimal import ROUND_HALF_UP, Decimal

MONEY_DECIMALS = 2
#: 9 decimales en la fraccion == 7 decimales cuando la tasa se muestra en %,
#: que es la precision minima que pide el enunciado.
RATE_DECIMALS = 9
RATE_PERCENT_DECIMALS = 7

MONEY_EXPONENT = Decimal(1).scaleb(-MONEY_DECIMALS)
RATE_EXPONENT = Decimal(1).scaleb(-RATE_DECIMALS)
RATE_PERCENT_EXPONENT = Decimal(1).scaleb(-RATE_PERCENT_DECIMALS)

ZERO_MONEY = Decimal("0.00")
ZERO_RATE = Decimal(0).quantize(RATE_EXPONENT)


def money(value: Decimal | int | str) -> Decimal:
    """Redondea un importe a 2 decimales (medio hacia arriba)."""
    return Decimal(value).quantize(MONEY_EXPONENT, rounding=ROUND_HALF_UP)


def rate(value: Decimal | int | str) -> Decimal:
    """Redondea una tasa (fraccion decimal) a 9 decimales."""
    return Decimal(value).quantize(RATE_EXPONENT, rounding=ROUND_HALF_UP)


def rate_percent(value: Decimal | int | str) -> Decimal:
    """Pasa una tasa en fraccion a porcentaje con 7 decimales: 0.006563965 -> 0.6563965."""
    return (Decimal(value) * 100).quantize(RATE_PERCENT_EXPONENT, rounding=ROUND_HALF_UP)


def percent_to_decimal(value: Decimal | int | str) -> Decimal:
    """40.00 (%) -> 0.40. Sin redondear: la division queda en precision plena."""
    return Decimal(value) / Decimal(100)


def decimal_to_percent(value: Decimal | int | str) -> Decimal:
    """0.0065644 -> 0.65644 (%)."""
    return Decimal(value) * Decimal(100)
