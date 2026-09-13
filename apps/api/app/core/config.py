"""App settings and business rules.

Everything the business might want to retune lives here instead of being
sprinkled across modules. Override with env vars (PRESTAMEAMI_ prefix).
"""

from decimal import Decimal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/ is the backend root, so the db path never depends on your cwd.
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRESTAMEAMI_", env_file=".env")

    app_name: str = "Prestameami.pe API"
    api_prefix: str = "/api"

    # ── Persistence ─────────────────────────────────────────────────────────
    database_url: str = f"sqlite:///{DATA_DIR / 'prestameami.db'}"

    # ── Session ─────────────────────────────────────────────────────────────
    # Academic single-admin app: locally signed token, no OAuth in sight.
    secret_key: str = "prestameami-dev-secret-no-usar-en-produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # ── Credit rules ────────────────────────────────────────────────────────
    currency: str = "PEN"
    currency_symbol: str = "S/"
    max_credit_amount: Decimal = Decimal("200.00")
    max_term_days: int = 14
    min_term_days: int = 1
    days_per_year: int = 360  # academic financial year
    money_decimals: int = 2
    rate_decimals: int = 9  # decimal fraction; that's 7 decimals once shown as %
    rate_percent_decimals: int = 7

    # Prefilled TEA on the new-credit form; the user can still change it.
    default_annual_rate: Decimal = Decimal("40.00")

    # Late-payment rate: 2% monthly (TEM). Deliberately NOT an ERD column — it is
    # a system-wide parameter, same for every credit. Prorated over days late on
    # a 30-day base.
    late_monthly_rate: Decimal = Decimal("0.02")
    late_rate_base_days: int = 30

    # How many overdue installments it takes to block a client.
    overdue_installments_to_block: int = 1

    # Accidental-resubmit window. An identical write inside this many seconds is
    # refused unless the caller insists explicitly.
    #
    # Kept deliberately tight: a double click or a retry lands within
    # milliseconds, while a human collecting the same amount twice takes minutes.
    # A wider window would start flagging legitimate repeat collections.
    duplicate_window_seconds: int = 15

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
