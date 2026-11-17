"""USER - the bodega owner/admin. Never represents a borrower."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core import clock
from app.core.enums import UserRole, UserStatus
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, validate_strings=True, length=20),
        default=UserRole.admin,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, native_enum=False, validate_strings=True, length=20),
        default=UserStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=clock.now)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
