"""First boot of a fresh database: create the administrator, optionally the demo.

Runs on every API start but only acts while the users table is empty, so a
deployed database is set up once and then left alone. Nothing here ever drops
or rewrites existing data - that's what scripts/seed.py is for, locally.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User

log = logging.getLogger("prestameami.bootstrap")


def bootstrap(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(User)):
        return

    if settings.seed_demo_data:
        # Same demo the README describes, built by the real services.
        from scripts.seed import seed

        seed(session)
        admin = session.scalars(select(User)).one()
        log.info("Base vacia: se cargaron los datos de demostracion.")
    else:
        admin = User(name="", email="", password_hash="")
        session.add(admin)

    # The credentials always come from the environment, never from the seed.
    admin.name = settings.admin_name
    admin.email = settings.admin_email.strip().lower()
    admin.password_hash = hash_password(settings.admin_password)
    session.commit()
    log.info("Administrador creado: %s", admin.email)
