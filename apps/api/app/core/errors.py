"""Errores de reglas de negocio.

Cada error lleva un `code` estable (para que el frontend lo traduzca con i18n)
y un `message` en espaniol que sirve de fallback y sale tal cual en Swagger.
"""

from typing import Any


class BusinessRuleError(Exception):
    """Regla de negocio incumplida. El router la convierte en HTTP 422."""

    status_code = 422

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class NotFoundError(BusinessRuleError):
    """El recurso pedido no existe. HTTP 404."""

    status_code = 404


class ConflictError(BusinessRuleError):
    """Choca con el estado actual del recurso. HTTP 409."""

    status_code = 409


class AuthError(BusinessRuleError):
    """Credenciales invalidas o sesion vencida. HTTP 401."""

    status_code = 401
