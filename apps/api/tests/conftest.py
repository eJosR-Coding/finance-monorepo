"""Shared pytest fixtures: an isolated database and a logged-in client."""

from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_session
from app.main import app
from app.models import User

ADMIN_EMAIL = "admin@prestameami.pe"
ADMIN_PASSWORD = "admin123"

TODAY = date(2026, 9, 12)


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Fresh in-memory database per test. StaticPool keeps it alive across connections."""
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
