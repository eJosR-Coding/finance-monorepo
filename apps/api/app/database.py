"""Database engine, sessions and the declarative Base."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import DATA_DIR, settings


class Base(DeclarativeBase):
    """Declarative base shared by every model."""


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # FastAPI hops across threads
    echo=False,
)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """SQLite ignores foreign keys unless you turn them on per connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_all() -> None:
    """Create the SQLite file and the tables if they aren't there yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Side-effecting import: this is what registers models on Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session
