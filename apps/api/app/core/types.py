"""Custom SQLAlchemy column types.

SQLite has no native decimal type: `Numeric` quietly stores floats and the
exactness dips. We persist Decimals as TEXT and hand them back as Decimal, so a
settled credit reads exactly 0.00 instead of 1.4e-17.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator


class DecimalText(TypeDecorator[Decimal]):
    """Fixed-precision Decimal persisted as TEXT."""

    impl = String
    cache_ok = True

    def __init__(self, decimals: int) -> None:
        super().__init__(length=32)
        self.decimals = decimals
        self._exponent = Decimal(1).scaleb(-decimals)

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(Decimal(value).quantize(self._exponent, rounding=ROUND_HALF_UP))

    def process_result_value(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value)


#: Amounts in soles (2 decimals).
MoneyColumn = DecimalText(2)
#: Effective rates as a decimal fraction; 9 decimals == 7 decimals in %.
RateColumn = DecimalText(9)
#: Annual rates written as a percentage (e.g. 40.00), 2 decimals.
PercentColumn = DecimalText(2)
