"""CLIENT - the neighbour who gets the fiado."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import clock
from app.core.enums import ClientCreditStatus
from app.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (CheckConstraint("length(dni) = 8", name="ck_client_dni_8_digits"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credit_status: Mapped[ClientCreditStatus] = mapped_column(
        SAEnum(ClientCreditStatus, native_enum=False, validate_strings=True, length=20),
        default=ClientCreditStatus.enabled,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=clock.now, onupdate=clock.now
    )

    credits: Mapped[list["Credit"]] = relationship(
        back_populates="client",
        cascade="save-update, merge", passive_deletes="all",
        order_by="Credit.id.desc()",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Client {self.dni} {self.full_name}>"
