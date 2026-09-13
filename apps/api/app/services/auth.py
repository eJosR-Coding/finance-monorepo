"""Authentication: verify credentials and mint the session token."""

from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.core.security import create_access_token, verify_password
from app.models import User
from app.repositories import users as users_repo

INVALID_CREDENTIALS = "Correo o contrasenia incorrectos."


def authenticate(session: Session, email: str, password: str) -> tuple[User, str]:
    user = users_repo.get_by_email(session, email)
    # Same message either way: we don't leak which emails exist.
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("INVALID_CREDENTIALS", INVALID_CREDENTIALS)
    return user, create_access_token(str(user.id))
