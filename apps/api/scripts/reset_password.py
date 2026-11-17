"""Recover access: set a new password for the administrator (informe 6.2.1).

Prestameami.pe runs locally with no mail server, so "forgot my password" can't
send a link. Whoever has access to the machine resets it from here instead:

    uv run python scripts/reset_password.py admin@prestameami.pe NuevaClave123

The new password is stored as a bcrypt hash and the account is reactivated.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.enums import UserStatus  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal, create_all  # noqa: E402
from app.repositories import users as users_repo  # noqa: E402

MIN_LENGTH = 6


def reset(email: str, new_password: str) -> str:
    """Return a status message; raise SystemExit with a message on bad input."""
    if len(new_password) < MIN_LENGTH:
        raise SystemExit(f"La contrasenia debe tener al menos {MIN_LENGTH} caracteres.")
    create_all()
    with SessionLocal() as session:
        user = users_repo.get_by_email(session, email)
        if user is None:
            raise SystemExit(f"No existe un usuario con el correo {email}.")
        user.password_hash = hash_password(new_password)
        user.status = UserStatus.active
        session.commit()
    return f"Contrasenia actualizada para {email}. Ya puedes iniciar sesion."


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Uso: uv run python scripts/reset_password.py <correo> <nueva_contrasenia>"
        )
    print(reset(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
