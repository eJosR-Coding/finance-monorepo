"""Payment schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import PaymentMethod
from app.schemas.common import Money


class PaymentCreate(BaseModel):
    amount_received: Decimal = Field(gt=0, examples=["70.69"])
    payment_method: PaymentMethod = Field(default=PaymentMethod.cash)
    payment_date: date | None = Field(
        default=None, description="Si se omite, se usa la fecha de hoy."
    )
    installment_id: int | None = Field(
        default=None,
        description="Cuota a cobrar. Si se omite, se aplica a la cuota pendiente mas antigua.",
    )
    notes: str | None = Field(default=None, max_length=500)
    allow_duplicate: bool = Field(
        default=False,
        description=(
            "Confirma a proposito un pago identico a uno reciente. "
            "Sin esto, un reenvio accidental se rechaza."
        ),
    )


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    credit_id: int
    installment_id: int
    payment_date: date
    amount_received: Money
    late_interest_amount: Money
    compensatory_interest_amount: Money
    principal_amount: Money
    remaining_balance: Money
    payment_method: PaymentMethod
    notes: str | None
    created_at: datetime


class PaymentListItem(PaymentRead):
    """A payment plus the context the global list needs to be readable."""

    credit_code: str
    client_id: int
    client_name: str


class PaymentAllocation(BaseModel):
    """How much of the payment hit each component, installment by installment."""

    installment_id: int
    installment_number: int
    late_interest_amount: Money
    compensatory_interest_amount: Money
    principal_amount: Money
    total_applied: Money
    installment_status: str


class PaymentPreview(BaseModel):
    """How an amount would split, without recording anything."""

    amount_received: Money
    due_amount: Money = Field(description="Saldo exigible de la cuota objetivo, con mora incluida.")
    late_interest_amount: Money
    compensatory_interest_amount: Money
    principal_amount: Money
    total_applied: Money
    remaining_balance: Money = Field(description="Saldo del credito despues del pago.")
    unapplied_amount: Money = Field(description="Excedente que la deuda no alcanza a absorber.")
    outcome: str = Field(description="exact | partial | surplus")
    days_late: int
    allocations: list[PaymentAllocation]


class PaymentResult(BaseModel):
    """Result of actually recording a payment."""

    credit_id: int
    payment_date: date
    amount_received: Money
    late_interest_amount: Money
    compensatory_interest_amount: Money
    principal_amount: Money
    remaining_balance: Money
    credit_status: str
    client_credit_status: str
    allocations: list[PaymentAllocation]
    payments: list[PaymentRead]
