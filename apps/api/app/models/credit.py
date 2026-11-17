"""CREDIT - a granted fiado with its financial terms frozen at grant time."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import clock
from app.core.config import settings
from app.core.enums import CreditStatus, GraceType, RateType
from app.core.types import MoneyColumn, PercentColumn, RateColumn
from app.database import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.installment import Installment
    from app.models.payment import Payment


class Credit(Base):
    __tablename__ = "credits"
    # Informe 8.3 / 8.7: product limits enforced by the database too, not only
    # by the service. Amounts are TEXT (see core/types.py), hence the CASTs.
    __table_args__ = (
        CheckConstraint(
            f"CAST(amount AS REAL) > 0 AND CAST(amount AS REAL) <= {settings.max_credit_amount}",
            name="ck_credit_amount_range",
        ),
        CheckConstraint(
            f"term_days BETWEEN {settings.min_term_days} AND {settings.max_term_days}",
            name="ck_credit_term_range",
        ),
        CheckConstraint("installments_count >= 1", name="ck_credit_installments_min"),
        CheckConstraint("payment_frequency_days >= 1", name="ck_credit_frequency_min"),
        CheckConstraint("grace_days >= 0", name="ck_credit_grace_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )

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
        cascade="save-update, merge",
        passive_deletes="all",
        order_by="Installment.installment_number",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="credit",
        cascade="save-update, merge",
        passive_deletes="all",
        order_by="Payment.id",
    )

    @property
    def code(self) -> str:
        """Display code (CR-0021). Derived from the id - not a stored column."""
        return f"CR-{self.id:04d}"

    def __repr__(self) -> str:
        return f"<Credit {self.code} {self.amount}>"
