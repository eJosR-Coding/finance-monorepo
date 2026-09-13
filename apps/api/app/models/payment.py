"""PAYMENT — un cobro registrado y como se repartio entre mora, interes y capital."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import clock
from app.core.enums import PaymentMethod
from app.core.types import MoneyColumn
from app.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.installment import Installment


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credits.id", ondelete="CASCADE"), index=True)
    installment_id: Mapped[int] = mapped_column(
        ForeignKey("installments.id", ondelete="CASCADE"), index=True
    )

    payment_date: Mapped[date] = mapped_column(Date)
    amount_received: Mapped[Decimal] = mapped_column(MoneyColumn)

    # Reparto academico obligatorio: mora -> interes compensatorio -> capital.
    late_interest_amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    compensatory_interest_amount: Mapped[Decimal] = mapped_column(MoneyColumn)
    principal_amount: Mapped[Decimal] = mapped_column(MoneyColumn)

    remaining_balance: Mapped[Decimal] = mapped_column(MoneyColumn)  # saldo del credito despues

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, native_enum=False, validate_strings=True, length=10)
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now)

    credit: Mapped["Credit"] = relationship(back_populates="payments")
    installment: Mapped["Installment"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.amount_received} on credit {self.credit_id}>"
