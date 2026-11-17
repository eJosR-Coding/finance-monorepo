"""App settings and business rules.

Everything the business might want to retune lives here instead of being
sprinkled across modules. Override with env vars (PRESTAMEAMI_ prefix).
"""

from decimal import Decimal
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/ is the backend root, so the db path never depends on your cwd.
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRESTAMEAMI_", env_file=".env")

    app_name: str = "Prestameami.pe API"
    api_prefix: str = "/api"

    # ── Persistence ─────────────────────────────────────────────────────────
    # Local: a SQLite file. Deployed: PostgreSQL (Neon), passed in as
    # PRESTAMEAMI_DATABASE_URL. Both run the same models and constraints.
    database_url: str = f"sqlite:///{DATA_DIR / 'prestameami.db'}"

    # ── First boot ──────────────────────────────────────────────────────────
    # When the users table is empty the API creates the administrator. With
    # seed_demo_data it loads the demo clients and credits too (for the
    # presentation). It never runs again once a user exists.
    admin_name: str = "Carlos Mendoza"
    admin_email: str = "admin@prestameami.pe"
    admin_password: str = "admin123"
    seed_demo_data: bool = False

    # ── Frontend ────────────────────────────────────────────────────────────
    # When the built SPA exists (apps/web/dist), the API serves it too, so a
    # deploy is one service and one URL. Locally Vite serves it instead.
    web_dist_dir: Path = BASE_DIR.parent / "web" / "dist"

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

    # RN-08: BCRP maximum conventional compensatory rate (effective annual, %).
    # For operations between parties outside the financial system it equals the
    # cap for national-currency loans. 114.13 % was in force from 01/05/2026 to
    # 31/10/2026; the BCRP republishes it every six months, so it is a setting
    # (PRESTAMEAMI_MAX_LEGAL_ANNUAL_RATE), never a constant in the formulas.
    max_legal_annual_rate: Decimal = Decimal("114.13")

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

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Neon and Render hand out postgres:// URLs; SQLAlchemy wants a driver."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
