"""Types shared across schemas.

Amounts travel as strings ("140.00") rather than numbers, so the JSON keeps
exact decimal precision and the frontend never runs them through a float.
"""

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, PlainSerializer

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{Decimal(v):.2f}", return_type=str, when_used="json"),
]
"""Amount in soles, serialized with 2 decimals."""

Rate = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{Decimal(v):.9f}", return_type=str, when_used="json"),
]
"""Rate as a decimal fraction, 9 decimals."""

Percent = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{Decimal(v):.2f}", return_type=str, when_used="json"),
]
"""Annual rate as a percentage, 2 decimals (40.00)."""

RatePercent = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{Decimal(v):.7f}", return_type=str, when_used="json"),
]
"""Periodic rate as a percentage, 7 decimals (0.6563965)."""


class ErrorResponse(BaseModel):
    """Uniform API error body."""

    code: str = Field(description="Codigo estable del error, para traducir en el frontend.")
    message: str = Field(description="Mensaje en espaniol listo para mostrar.")
    details: dict[str, Any] = Field(default_factory=dict)
