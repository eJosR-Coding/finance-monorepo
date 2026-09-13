"""CLIENT — la persona de la bodega que recibe el fiado."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import clock
from app.core.enums import ClientCreditStatus
from app.database import Base

if TYPE_CHECKING:
    from app.models.credit import Credit


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(200))
    credit_status: Mapped[ClientCreditStatus] = mapped_column(
        SAEnum(ClientCreditStatus, native_enum=False, validate_strings=True, length=20),
        default=ClientCreditStatus.enabled,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=clock.now, onupdate=clock.now
    )

    credits: Mapped[list["Credit"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", order_by="Credit.id.desc()"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Client {self.dni} {self.full_name}>"
