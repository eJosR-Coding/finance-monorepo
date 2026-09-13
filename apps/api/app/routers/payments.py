"""Rutas de pagos, colgadas de un credito."""

from fastapi import APIRouter, status

from app.routers.deps import CurrentUser, SessionDep
from app.schemas.payment import (
    PaymentCreate,
    PaymentListItem,
    PaymentPreview,
    PaymentRead,
    PaymentResult,
)
from app.services import payments as payments_service

router = APIRouter(prefix="/credits/{credit_id}/payments", tags=["payments"])
all_payments_router = APIRouter(prefix="/payments", tags=["payments"])


@all_payments_router.get("", response_model=list[PaymentListItem], summary="Listar todos los pagos")
def list_all_payments(session: SessionDep, current_user: CurrentUser) -> list[PaymentListItem]:
    """Todos los cobros registrados, del mas reciente al mas antiguo."""
    return payments_service.list_all(session)


@router.get("", response_model=list[PaymentRead], summary="Historial de pagos del credito")
def list_payments(
    credit_id: int, session: SessionDep, current_user: CurrentUser
) -> list[PaymentRead]:
    """Pagos registrados del credito, del mas reciente al mas antiguo."""
    return payments_service.list_for_credit(session, credit_id)


@router.post(
    "",
    response_model=PaymentResult,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un pago",
)
def create_payment(
    credit_id: int, payload: PaymentCreate, session: SessionDep, current_user: CurrentUser
) -> PaymentResult:
    """Registra el pago y lo reparte en el orden academico obligatorio:

    1. interes moratorio
    2. interes compensatorio
    3. capital

    La respuesta detalla cuanto se aplico a cada componente y el saldo
    resultante del credito.
    """
    return payments_service.register(session, credit_id, payload)


@router.post("/preview", response_model=PaymentPreview, summary="Previsualizar un pago")
def preview_payment(
    credit_id: int, payload: PaymentCreate, session: SessionDep, current_user: CurrentUser
) -> PaymentPreview:
    """Muestra como se repartiria el monto recibido, sin registrar nada."""
    return payments_service.preview(session, credit_id, payload)
