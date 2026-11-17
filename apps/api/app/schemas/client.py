"""Client schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.core.enums import ClientCreditStatus
from app.schemas.common import Money
from app.schemas.credit import CreditListItem
from app.schemas.payment import PaymentRead


def _clean_phone(value: str | None) -> str | None:
    """Optional, 9 digits once spaces and dashes are dropped (informe 6.1.1)."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    digits = cleaned.replace(" ", "").replace("-", "")
    if not digits.isdigit() or len(digits) != 9:
        raise ValueError("El telefono debe tener 9 digitos.")
    return cleaned


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class ClientCreate(BaseModel):
    dni: str = Field(min_length=8, max_length=8, examples=["71456238"])
    first_name: str = Field(min_length=1, max_length=80, examples=["Maria"])
    last_name: str = Field(min_length=1, max_length=80, examples=["Torres"])
    phone: str | None = Field(default=None, max_length=15, examples=["987 234 521"])
    address: str | None = Field(
        default=None, max_length=255, examples=["Av. Los Jardines 245, Lima"]
    )

    @field_validator("dni")
    @classmethod
    def dni_must_be_numeric(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit():
            raise ValueError("El DNI debe tener 8 digitos numericos.")
        return cleaned

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Este campo es obligatorio.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        return _clean_phone(value)

    @field_validator("address")
    @classmethod
    def address_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ClientUpdate(BaseModel):
    """Partial update. Only the fields actually sent get touched.

    Phone and address are optional data: sending "" (or null) clears them.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=15)
    address: str | None = Field(default=None, max_length=255)
    credit_status: ClientCreditStatus | None = None

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        return _clean_phone(value)

    @field_validator("address")
    @classmethod
    def address_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dni: str
    first_name: str
    last_name: str
    phone: str | None
    address: str | None
    credit_status: ClientCreditStatus
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def initials(self) -> str:
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()


class ClientListItem(ClientRead):
    """Clients-table row: adds the derived fields the UI shows."""

    active_credits: int = 0
    outstanding_balance: Money
    last_movement_at: datetime | None = None


class ActivityItem(BaseModel):
    """Client timeline event. Derived on the fly, never stored in a table."""

    date: date
    type: Literal["client_created", "credit_created", "payment_registered"]
    title: str
    amount: Money | None = None
    credit_id: int | None = None


class ClientDetail(ClientListItem):
    """Full client file: summary, credits, payments and derived timeline."""

    total_paid: Money
    last_payment_date: date | None = None
    credits: list["CreditListItem"]
    payments: list["PaymentRead"]
    activity: list[ActivityItem]


class ClientListResponse(BaseModel):
    items: list[ClientListItem]
    total: int
