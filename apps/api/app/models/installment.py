"""INSTALLMENT — una fila del cronograma de amortizacion (metodo frances)."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InstallmentStatus
from app.core.types import MoneyColumn
from app.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.payment import Payment


class Installment(Base):
    __tablename__ = "installments"
    __table_args__ = (
        UniqueConstraint(
            "credit_id", "installment_number", name="uq_installment_number_per_credit"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credits.id", ondelete="CASCADE"), index=True)

    installment_number: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date)

    opening_balance: Mapped[Decimal] = mapped_column(MoneyColumn)
    interest_amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    amortization_amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    installment_amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    closing_balance: Mapped[Decimal] = mapped_column(MoneyColumn)

    status: Mapped[InstallmentStatus] = mapped_column(
        SAEnum(InstallmentStatus, native_enum=False, validate_strings=True, length=10),
        default=InstallmentStatus.pending,
    )

    credit: Mapped["Credit"] = relationship(back_populates="installments")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="installment", cascade="all, delete-orphan", order_by="Payment.id"
    )

    def __repr__(self) -> str:
        return f"<Installment #{self.installment_number} {self.installment_amount}>"
