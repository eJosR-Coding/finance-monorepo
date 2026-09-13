"""Motor de base de datos, sesiones y Base declarativa."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATA_DIR, settings


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos."""


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # FastAPI usa varios hilos
    echo=False,
)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """SQLite ignora las FK salvo que se activen en cada conexion."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_all() -> None:
    """Crea el archivo SQLite y las tablas si no existen."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Import con efecto secundario: registra los modelos en Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: una sesion por request."""
    with SessionLocal() as session:
        yield session
