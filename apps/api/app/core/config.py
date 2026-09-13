"""Configuracion de la aplicacion y reglas de negocio.

Todo lo que el negocio puede "retocar" vive aca, no hardcodeado por ahi.
Se puede sobreescribir con variables de entorno (prefijo PRESTAMEAMI_).
"""

from decimal import Decimal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/  -> raiz del backend. Asi la DB no depende del cwd desde donde corras.
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRESTAMEAMI_", env_file=".env")

    app_name: str = "Prestameami.pe API"
    api_prefix: str = "/api"

    # ── Persistencia ────────────────────────────────────────────────────────
    database_url: str = f"sqlite:///{DATA_DIR / 'prestameami.db'}"

    # ── Sesion ──────────────────────────────────────────────────────────────
    # App academica de un solo administrador: token firmado local, sin OAuth.
    secret_key: str = "prestameami-dev-secret-no-usar-en-produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # ── Reglas de credito ───────────────────────────────────────────────────
    currency: str = "PEN"
    currency_symbol: str = "S/"
    max_credit_amount: Decimal = Decimal("200.00")
    max_term_days: int = 14
    min_term_days: int = 1
    days_per_year: int = 360  # anio financiero academico
    money_decimals: int = 2
    rate_decimals: int = 9  # fraccion decimal; equivale a 7 decimales en %
    rate_percent_decimals: int = 7

    # TEA sugerida en el formulario de nuevo credito (el usuario puede cambiarla).
    default_annual_rate: Decimal = Decimal("40.00")

    # Tasa moratoria: 2% mensual (TEM). No es columna del ERD — es parametro del
    # sistema, igual para todos los creditos. Se convierte a la cantidad de dias
    # de atraso con base 30.
    late_monthly_rate: Decimal = Decimal("0.02")
    late_rate_base_days: int = 30

    # Cuantas cuotas vencidas bastan para bloquear al cliente.
    overdue_installments_to_block: int = 1

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
