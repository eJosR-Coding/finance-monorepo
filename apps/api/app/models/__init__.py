"""Modelos ORM. El import de todos aca es lo que puebla `Base.metadata`."""

from app.models.client import Client
from app.models.credit import Credit
from app.models.installment import Installment
from app.models.payment import Payment
from app.models.user import User

__all__ = ["Client", "Credit", "Installment", "Payment", "User"]
