"""Rutas de dashboard, morosidad y parametros del sistema."""

from fastapi import APIRouter

from app.core.config import settings
from app.routers.deps import CurrentUser, SessionDep
from app.schemas.dashboard import ConfigResponse, DashboardResponse, OverdueResponse
from app.services import dashboard as dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Resumen del negocio")
def dashboard(session: SessionDep, current_user: CurrentUser) -> DashboardResponse:
    """Creditos activos, saldo por cobrar, cobros de hoy y proximos vencimientos."""
    return dashboard_service.build(session)


@router.get("/overdue", response_model=OverdueResponse, summary="Morosos y cuotas vencidas")
def overdue(session: SessionDep, current_user: CurrentUser) -> OverdueResponse:
    """Cuotas vencidas con dias de mora, saldo vencido e interes moratorio."""
    return dashboard_service.overdue_report(session)


@router.get("/config", response_model=ConfigResponse, summary="Parametros del sistema")
def config() -> ConfigResponse:
    """Limites y tasas vigentes. El frontend los usa para validar y mostrar ayudas."""
    return ConfigResponse(
        currency=settings.currency,
        currency_symbol=settings.currency_symbol,
        max_credit_amount=settings.max_credit_amount,
        min_term_days=settings.min_term_days,
        max_term_days=settings.max_term_days,
        days_per_year=settings.days_per_year,
        money_decimals=settings.money_decimals,
        rate_percent_decimals=settings.rate_percent_decimals,
        default_annual_rate=settings.default_annual_rate,
        late_monthly_rate_percent=settings.late_monthly_rate * 100,
        overdue_installments_to_block=settings.overdue_installments_to_block,
    )
