"""Credit schemas: simulation, creation and reads."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import settings
from app.core.enums import CreditStatus, GraceType, InstallmentStatus, RateType
from app.schemas.common import Money, Percent, Rate, RatePercent


class CreditTerms(BaseModel):
    """Terms that define a credit. Shared by simulate and create."""

    client_id: int = Field(examples=[1])
    amount: Decimal = Field(gt=0, examples=["140.00"])
    rate_type: RateType = Field(default=RateType.TEA)
    annual_rate: Decimal = Field(
        ge=0, examples=["40.00"], description="En porcentaje: 40.00 = 40 %"
    )
    start_date: date = Field(examples=["2026-09-12"])
    term_days: int = Field(ge=1, examples=[14])
    installments_count: int = Field(ge=1, examples=[2])
    payment_frequency_days: int = Field(ge=1, examples=[7])
    grace_type: GraceType = Field(default=GraceType.none)
    grace_days: int = Field(default=0, ge=0)


class SimulationRequest(CreditTerms):
    """Client is optional when simulating - you may be shopping terms first."""

    client_id: int | None = Field(default=None, examples=[1])


class ScheduleRowRead(BaseModel):
    installment_number: int
    due_date: date
    opening_balance: Money
    interest: Money
    amortization: Money
    installment: Money
    closing_balance: Money


class SimulationResponse(BaseModel):
    """Simulator output. Persists nothing."""

    amount: Money
    financed_principal: Money
    rate_type: RateType
    annual_rate: Percent
    periodic_rate: Rate
    periodic_rate_percent: RatePercent
    installment_amount: Money
    total_interest: Money
    total_payment: Money
    final_balance: Money
    tcea: Percent
    term_days: int
    installments_count: int
    payment_frequency_days: int
    grace_type: GraceType
    grace_days: int
    late_monthly_rate_percent: Percent = Field(
        default=settings.late_monthly_rate * 100,
        description="Tasa moratoria mensual vigente en el sistema.",
    )
    schedule: list[ScheduleRowRead]


class InstallmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    installment_number: int
    due_date: date
    opening_balance: Money
    interest_amount: Money
    amortization_amount: Money
    installment_amount: Money
    closing_balance: Money
    status: InstallmentStatus
    paid_amount: Money = Decimal("0.00")
    outstanding_amount: Money = Decimal("0.00")
    days_late: int = 0


class CreditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    amount: Money
    start_date: date
    term_days: int
    rate_type: RateType
    annual_rate: Percent
    periodic_rate: Rate
    installments_count: int
    payment_frequency_days: int
    grace_type: GraceType
    grace_days: int
    total_interest: Money
    total_payment: Money
    outstanding_balance: Money
    status: CreditStatus
    created_at: datetime

    @computed_field
    @property
    def code(self) -> str:
        return f"CR-{self.id:04d}"

    @computed_field
    @property
    def periodic_rate_percent(self) -> str:
        return f"{self.periodic_rate * 100:.7f}"


class CreditListItem(CreditRead):
    client_name: str
    next_due_date: date | None = None


class CreditDetail(CreditListItem):
    client_dni: str
    client_credit_status: str
    installment_amount: Money
    tcea: Percent
    late_monthly_rate_percent: Percent
    installments: list[InstallmentRead]


class CreditListResponse(BaseModel):
    items: list[CreditListItem]
    total: int
