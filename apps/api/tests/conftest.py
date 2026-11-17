"""Shared pytest fixtures: an isolated database and a logged-in client.

By default every test gets a fresh in-memory SQLite. To run the very same
suite against PostgreSQL (what the deploy uses), point it at an empty database:

    PRESTAMEAMI_TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test uv run pytest
"""

import os

# Before importing the app: its module-level engine must never touch the real
# local database (apps/api/data/prestameami.db) while tests run.
os.environ["PRESTAMEAMI_DATABASE_URL"] = "sqlite://"
os.environ["PRESTAMEAMI_SEED_DEMO_DATA"] = "false"

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import clock
from app.core.config import Settings, settings
from app.core.security import hash_password
from app.database import Base, get_session
from app.main import app
from app.models import User

TEST_DATABASE_URL = os.environ.get("PRESTAMEAMI_TEST_DATABASE_URL", "")

ADMIN_EMAIL = "admin@prestameami.pe"
ADMIN_PASSWORD = "admin123"

TODAY = date(2026, 9, 12)


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch: pytest.MonkeyPatch) -> date:
    """Pin the business date the services read, so the suite never rots.

    The fixtures build credits starting on TODAY. Without this, once the real
    calendar passes their due dates every one of them turns overdue and the
    assertions about 'active' / 'pending' fail for reasons unrelated to the code.
    Only `today` is pinned: `now` stays real so the resubmit window still works.
    """
    monkeypatch.setattr(clock, "today", lambda: TODAY)
    return TODAY


@pytest.fixture
def no_legal_rate_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lift the BCRP cap for tests that stress the pure math with extreme rates."""
    monkeypatch.setattr(settings, "max_legal_annual_rate", Decimal("100000"))


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Fresh database per test. StaticPool keeps in-memory SQLite alive across connections."""
    if TEST_DATABASE_URL:
        engine = create_engine(Settings(database_url=TEST_DATABASE_URL).database_url)
        Base.metadata.drop_all(engine)
    else:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        db.add(
            User(
                name="Carlos Mendoza",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
        )
        db.commit()
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Standalone session for tests that poke the database directly."""
    with session_factory() as db:
        yield db


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient, None, None]:
    """Unauthenticated API client wired to the test database.

    One session PER REQUEST, same as production - sharing a single session
    across requests leaves stale relationships in the identity map and the
    assertions go sideways.
    """

    def override() -> Generator[Session, None, None]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """API client that already carries the admin's bearer token."""
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def client_id(auth_client: TestClient) -> int:
    """A registered, enabled borrower ready to receive credit."""
    response = auth_client.post(
        "/api/clients",
        json={
            "dni": "71456238",
            "first_name": "Maria",
            "last_name": "Torres",
            "phone": "987 234 521",
            "address": "Av. Los Jardines 245, Lima",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
