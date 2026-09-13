"""CREDIT — un fiado otorgado, con sus condiciones financieras congeladas."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import clock
from app.core.enums import CreditStatus, GraceType, RateType
from app.core.types import MoneyColumn, PercentColumn, RateColumn
from app.database import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.installment import Installment
    from app.models.payment import Payment


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)

    amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    start_date: Mapped[date] = mapped_column(Date)
    term_days: Mapped[int] = mapped_column(Integer)

    rate_type: Mapped[RateType] = mapped_column(
        SAEnum(RateType, native_enum=False, validate_strings=True, length=10)
    )
    annual_rate: Mapped[Decimal] = mapped_column(PercentColumn)  # en %, ej. 40.00
    periodic_rate: Mapped[Decimal] = mapped_column(RateColumn)  # decimal, 7 dp

    installments_count: Mapped[int] = mapped_column(Integer)
    payment_frequency_days: Mapped[int] = mapped_column(Integer)

    grace_type: Mapped[GraceType] = mapped_column(
        SAEnum(GraceType, native_enum=False, validate_strings=True, length=10),
        default=GraceType.none,
    )
    grace_days: Mapped[int] = mapped_column(Integer, default=0)

    total_interest: Mapped[Decimal] = mapped_column(MoneyColumn)
    total_payment: Mapped[Decimal] = mapped_column(MoneyColumn)
    outstanding_balance: Mapped[Decimal] = mapped_column(MoneyColumn)

    status: Mapped[CreditStatus] = mapped_column(
        SAEnum(CreditStatus, native_enum=False, validate_strings=True, length=10),
        default=CreditStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now)

    client: Mapped["Client"] = relationship(back_populates="credits")
    installments: Mapped[list["Installment"]] = relationship(
        back_populates="credit",
        cascade="all, delete-orphan",
        order_by="Installment.installment_number",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="credit", cascade="all, delete-orphan", order_by="Payment.id"
    )

    @property
    def code(self) -> str:
        """Codigo visible del credito (CR-0021). Se deriva del id, no es columna."""
        return f"CR-{self.id:04d}"

    def __repr__(self) -> str:
        return f"<Credit {self.code} {self.amount}>"
