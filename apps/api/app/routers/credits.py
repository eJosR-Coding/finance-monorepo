"""Rutas de creditos: simulacion, otorgamiento y consulta."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.enums import CreditStatus
from app.routers.deps import CurrentUser, SessionDep
from app.schemas.credit import (
    CreditDetail,
    CreditListResponse,
    CreditTerms,
    SimulationRequest,
    SimulationResponse,
)
from app.services import credits as credits_service

router = APIRouter(prefix="/credits", tags=["credits"])


@router.post("/simulate", response_model=SimulationResponse, summary="Simular un credito")
def simulate(payload: SimulationRequest, current_user: CurrentUser) -> SimulationResponse:
    """Calcula el cronograma frances sin guardar nada.

    Devuelve la tasa periodica, la cuota, el interes total, el total a pagar y
    el cronograma completo con saldo final en cero.
    """
    return credits_service.simulate(payload)


@router.post(
    "",
    response_model=CreditDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Otorgar un credito",
)
def create_credit(
    payload: CreditTerms, session: SessionDep, current_user: CurrentUser
) -> CreditDetail:
    """Valida al cliente, calcula el cronograma y persiste credito y cuotas.

    Rechaza el otorgamiento si el cliente esta bloqueado o mantiene una deuda
    vencida. Todo se guarda en una sola transaccion.
    """
    credit = credits_service.create(session, payload)
    return credits_service.get_detail(session, credit.id)


@router.get("", response_model=CreditListResponse, summary="Listar creditos")
def list_credits(
    session: SessionDep,
    current_user: CurrentUser,
    client_id: Annotated[int | None, Query(description="Filtra por cliente.")] = None,
    status_filter: Annotated[CreditStatus | None, Query(alias="status")] = None,
) -> CreditListResponse:
    """Lista los creditos otorgados, del mas reciente al mas antiguo."""
    items = credits_service.list_credits(session, client_id=client_id, status=status_filter)
    return CreditListResponse(items=items, total=len(items))


@router.get("/{credit_id}", response_model=CreditDetail, summary="Detalle del credito")
def get_credit(credit_id: int, session: SessionDep, current_user: CurrentUser) -> CreditDetail:
    """Condiciones del credito y su cronograma de amortizacion completo."""
    return credits_service.get_detail(session, credit_id)
