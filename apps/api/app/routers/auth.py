"""Rutas de autenticacion."""

from fastapi import APIRouter

from app.routers.deps import CurrentUser, SessionDep
from app.schemas.auth import LoginRequest, TokenResponse, UserRead
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesion")
def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    """Valida las credenciales del administrador y devuelve el token de sesion."""
    user, token = auth_service.authenticate(session, payload.email, payload.password)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead, summary="Usuario de la sesion actual")
def me(current_user: CurrentUser) -> UserRead:
    """Devuelve el administrador dueño del token enviado."""
    return UserRead.model_validate(current_user)
