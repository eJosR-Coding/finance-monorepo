"""Business-rule errors.

Each error carries a stable `code` (so the frontend can translate it via i18n)
plus a Spanish `message` that works as a fallback and shows up in Swagger.
"""

from typing import Any


class BusinessRuleError(Exception):
    """A business rule was broken. The router turns this into HTTP 422."""

    status_code = 422

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class NotFoundError(BusinessRuleError):
    """Requested resource does not exist. HTTP 404."""

    status_code = 404


class ConflictError(BusinessRuleError):
    """Conflicts with the resource's current state. HTTP 409."""

    status_code = 409


class AuthError(BusinessRuleError):
    """Bad credentials or an expired session. HTTP 401."""

    status_code = 401
