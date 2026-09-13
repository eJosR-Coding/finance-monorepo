"""Enumeraciones del dominio. Los valores son exactamente los del ERD."""

from enum import Enum


class ClientCreditStatus(str, Enum):
    enabled = "enabled"
    blocked = "blocked"


class RateType(str, Enum):
    TNA = "TNA"
    TEA = "TEA"


class GraceType(str, Enum):
    none = "none"
    partial = "partial"
    total = "total"


class CreditStatus(str, Enum):
    active = "active"
    paid = "paid"
    overdue = "overdue"


class InstallmentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


class PaymentMethod(str, Enum):
    cash = "cash"
    yape = "yape"
    plin = "plin"
    transfer = "transfer"
