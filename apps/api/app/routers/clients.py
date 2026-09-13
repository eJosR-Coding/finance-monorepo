"""Rutas de clientes."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.enums import ClientCreditStatus
from app.repositories import payments as payments_repo
from app.routers.deps import CurrentUser, SessionDep
from app.schemas.client import (
    ClientCreate,
    ClientDetail,
    ClientListResponse,
    ClientRead,
    ClientUpdate,
)
from app.schemas.payment import PaymentRead
from app.services import clients as clients_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=ClientListResponse, summary="Listar clientes")
def list_clients(
    session: SessionDep,
    current_user: CurrentUser,
    search: Annotated[str | None, Query(description="Busca por nombre o DNI.")] = None,
    status_filter: Annotated[ClientCreditStatus | None, Query(alias="status")] = None,
    sort: Annotated[str, Query(pattern="^(recent|debt)$")] = "recent",
) -> ClientListResponse:
    """Devuelve los clientes con su saldo pendiente y estado crediticio."""
    items = clients_service.list_clients(session, search=search, status=status_filter, sort=sort)
    return ClientListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente",
)
def create_client(
    payload: ClientCreate, session: SessionDep, current_user: CurrentUser
) -> ClientRead:
    """Registra un cliente nuevo. El DNI no puede repetirse."""
    return ClientRead.model_validate(clients_service.create(session, payload))


@router.get("/{client_id}", response_model=ClientDetail, summary="Detalle del cliente")
def get_client(client_id: int, session: SessionDep, current_user: CurrentUser) -> ClientDetail:
    """Ficha del cliente: resumen, creditos, pagos e historial de actividad."""
    client = clients_service.get_client(session, client_id)
    base = clients_service.to_list_item(client)
    return ClientDetail(
        **base.model_dump(exclude={"full_name", "initials"}),
        total_paid=clients_service.total_paid(session, client_id),
        last_payment_date=clients_service.last_payment_date(session, client_id),
        credits=clients_service.list_credit_items(session, client_id),
        payments=[
            PaymentRead.model_validate(p)
            for p in payments_repo.list_by_client(session, client_id)
        ],
        activity=clients_service.build_activity(session, client),
    )


@router.patch("/{client_id}", response_model=ClientRead, summary="Actualizar cliente")
def update_client(
    client_id: int, payload: ClientUpdate, session: SessionDep, current_user: CurrentUser
) -> ClientRead:
    """Actualiza los datos de contacto o el estado crediticio del cliente."""
    return ClientRead.model_validate(clients_service.update(session, client_id, payload))
