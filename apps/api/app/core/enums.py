"""Enumeraciones del dominio. Los valores son exactamente los del ERD."""

from enum import StrEnum


class ClientCreditStatus(StrEnum):
    enabled = "enabled"
    blocked = "blocked"


class RateType(StrEnum):
    TNA = "TNA"
    TEA = "TEA"


class GraceType(StrEnum):
    none = "none"
    partial = "partial"
    total = "total"


class CreditStatus(StrEnum):
    active = "active"
    paid = "paid"
    overdue = "overdue"


class InstallmentStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


class PaymentMethod(StrEnum):
    cash = "cash"
    yape = "yape"
    plin = "plin"
    transfer = "transfer"
