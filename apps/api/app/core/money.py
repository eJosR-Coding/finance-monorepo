"""Money precision helpers.

House rule: money is Decimal, never float. Rounding happens ONLY at the end,
right before a number is stored or shown. Floats would leave us cooked with
0.30000000000000004 style residue.
"""

from decimal import ROUND_HALF_UP, Decimal

MONEY_DECIMALS = 2
#: 9 decimals on the fraction == 7 decimals once the rate is shown as a
#: percentage, which is the minimum precision the assignment asks for.
RATE_DECIMALS = 9
RATE_PERCENT_DECIMALS = 7

MONEY_EXPONENT = Decimal(1).scaleb(-MONEY_DECIMALS)
RATE_EXPONENT = Decimal(1).scaleb(-RATE_DECIMALS)
RATE_PERCENT_EXPONENT = Decimal(1).scaleb(-RATE_PERCENT_DECIMALS)

ZERO_MONEY = Decimal("0.00")
ZERO_RATE = Decimal(0).quantize(RATE_EXPONENT)


def money(value: Decimal | int | str) -> Decimal:
    """Round an amount to 2 decimals (half up)."""
    return Decimal(value).quantize(MONEY_EXPONENT, rounding=ROUND_HALF_UP)


def rate(value: Decimal | int | str) -> Decimal:
    """Round a rate (decimal fraction) to 9 decimals."""
    return Decimal(value).quantize(RATE_EXPONENT, rounding=ROUND_HALF_UP)


def rate_percent(value: Decimal | int | str) -> Decimal:
    """Fraction to percentage with 7 decimals: 0.006563965 -> 0.6563965."""
    return (Decimal(value) * 100).quantize(RATE_PERCENT_EXPONENT, rounding=ROUND_HALF_UP)


def percent_to_decimal(value: Decimal | int | str) -> Decimal:
    """40.00 (%) -> 0.40. No rounding here, the division keeps full precision."""
    return Decimal(value) / Decimal(100)


def decimal_to_percent(value: Decimal | int | str) -> Decimal:
    """0.0065644 -> 0.65644 (%)."""
    return Decimal(value) * Decimal(100)
