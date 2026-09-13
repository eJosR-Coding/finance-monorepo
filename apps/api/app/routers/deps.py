"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.core.security import decode_access_token
from app.database import get_session
from app.models import User
from app.repositories import users as users_repo

SessionDep = Annotated[Session, Depends(get_session)]

# auto_error=False so a missing header becomes our own 401 body, not Starlette's.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AuthError("NOT_AUTHENTICATED", "Debes iniciar sesion para continuar.")
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise AuthError("SESSION_EXPIRED", "Tu sesion expiro. Vuelve a iniciar sesion.")
    user = users_repo.get_by_id(session, int(subject))
    if user is None:
        raise AuthError("SESSION_EXPIRED", "Tu sesion expiro. Vuelve a iniciar sesion.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
