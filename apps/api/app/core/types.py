"""Tipos de columna para SQLAlchemy.

SQLite no tiene tipo decimal nativo: si se usa `Numeric` guarda floats y se
pierde exactitud. Guardamos los Decimal como TEXTO y los devolvemos como
Decimal, asi el saldo final es exactamente 0.00 y no 1.4e-17.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator


class DecimalText(TypeDecorator[Decimal]):
    """Decimal de precision fija persistido como TEXT."""

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


#: Importes en soles (2 decimales).
MoneyColumn = DecimalText(2)
#: Tasas efectivas como fraccion decimal, 9 decimales == 7 decimales en %.
RateColumn = DecimalText(9)
#: Tasas anuales expresadas en porcentaje (ej. 40.00), 2 decimales.
PercentColumn = DecimalText(2)
