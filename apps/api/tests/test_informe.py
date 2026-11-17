"""Reglas del informe (secciones 5.1.7, 6.1, 6.2.2 y 8) que antes no se cumplian.

Tasa maxima legal del BCRP (RN-08), datos opcionales del cliente, rol y estado
del usuario, indicadores del dashboard y restricciones de integridad de la base.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import CreditStatus, GraceType, RateType, UserStatus
from app.core.errors import BusinessRuleError
from app.models import Client, Credit, Payment, User
from app.services import finance
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, TODAY

CAP = settings.max_legal_annual_rate


def _schedule(rate_type: RateType, annual: str, frequency: int = 7):
    return finance.build_schedule(
        amount=Decimal("100.00"),
        rate_type=rate_type,
        annual_rate=Decimal(annual),
        start_date=TODAY,
        term_days=14,
        installments_count=14 // frequency,
        payment_frequency_days=frequency,
        grace_type=GraceType.none,
    )


# ── RN-08: tasa maxima legal del BCRP ──────────────────────────────────────


def test_tea_igual_al_tope_legal_se_acepta() -> None:
    assert _schedule(RateType.TEA, str(CAP)).final_balance == Decimal("0.00")


def test_tea_por_encima_del_tope_legal_se_rechaza() -> None:
    with pytest.raises(BusinessRuleError) as error:
        _schedule(RateType.TEA, str(CAP + Decimal("0.01")))
    assert error.value.code == "RATE_ABOVE_LEGAL_MAX"


def test_la_tna_se_compara_por_su_tea_equivalente() -> None:
    """TNA 80 % capitalizable cada 7 dias equivale a una TEA de ~121 %: excede."""
    effective = finance.effective_annual_rate(RateType.TNA, Decimal("80.00"), 7)
    assert effective > CAP
    with pytest.raises(BusinessRuleError) as error:
        _schedule(RateType.TNA, "80.00")
    assert error.value.code == "RATE_ABOVE_LEGAL_MAX"


def test_una_tna_cuya_tea_queda_bajo_el_tope_se_acepta() -> None:
    effective = finance.effective_annual_rate(RateType.TNA, Decimal("70.00"), 7)
    assert effective < CAP
    assert _schedule(RateType.TNA, "70.00").final_balance == Decimal("0.00")


def test_conversion_tna_a_tea_usa_la_formula_del_informe() -> None:
    """6.3.3: TEA = (1 + j/m)^m - 1, con m = 360 / frecuencia."""
    j, days = Decimal("0.60"), 7
    m = Decimal(360) / Decimal(days)
    expected = ((1 + j / m) ** m - 1) * 100
    assert finance.effective_annual_rate(RateType.TNA, Decimal("60.00"), days) == expected


def test_el_tope_es_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_legal_annual_rate", Decimal("30.00"))
    with pytest.raises(BusinessRuleError):
        _schedule(RateType.TEA, "40.00")


def test_la_api_rechaza_la_simulacion_sobre_el_tope(
    auth_client: TestClient, client_id: int
) -> None:
    response = auth_client.post(
        "/api/credits/simulate",
        json={
            "client_id": client_id,
            "amount": "100.00",
            "rate_type": "TEA",
            "annual_rate": "150.00",
            "start_date": TODAY.isoformat(),
            "term_days": 14,
            "installments_count": 2,
            "payment_frequency_days": 7,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "RATE_ABOVE_LEGAL_MAX"
    assert body["details"]["max_legal_annual_rate"] == str(CAP)


def test_config_expone_el_tope_legal(client: TestClient) -> None:
    body = client.get("/api/config").json()
    assert Decimal(body["max_legal_annual_rate"]) == CAP


# ── Cliente: telefono y direccion opcionales (6.1.1 y 8.2) ────────────────


def test_cliente_sin_telefono_ni_direccion(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/clients", json={"dni": "40111222", "first_name": "Rosa", "last_name": "Quispe"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["phone"] is None
    assert response.json()["address"] is None


@pytest.mark.parametrize("phone", ["98723452", "9872345210", "98a234521"])
def test_telefono_debe_tener_9_digitos(auth_client: TestClient, phone: str) -> None:
    response = auth_client.post(
        "/api/clients",
        json={"dni": "40111223", "first_name": "Rosa", "last_name": "Quispe", "phone": phone},
    )
    assert response.status_code == 422


def test_un_null_explicito_no_borra_el_nombre(auth_client: TestClient, client_id: int) -> None:
    response = auth_client.patch(f"/api/clients/{client_id}", json={"first_name": None})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Maria"


def test_vaciar_el_telefono_lo_deja_en_null(auth_client: TestClient, client_id: int) -> None:
    response = auth_client.patch(f"/api/clients/{client_id}", json={"phone": ""})
    assert response.status_code == 200
    assert response.json()["phone"] is None


# ── Usuario: rol y estado (8.1) ────────────────────────────────────────────


def test_el_login_devuelve_rol_y_estado(client: TestClient) -> None:
    body = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    ).json()
    assert body["user"]["role"] == "admin"
    assert body["user"]["status"] == "active"


def test_un_usuario_inactivo_no_puede_ingresar(client: TestClient, session: Session) -> None:
    user = session.scalars(select(User)).one()
    user.status = UserStatus.inactive
    session.commit()
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "USER_INACTIVE"


def test_desactivar_al_usuario_corta_su_sesion(
    auth_client: TestClient, session: Session
) -> None:
    user = session.scalars(select(User)).one()
    user.status = UserStatus.inactive
    session.commit()
    assert auth_client.get("/api/auth/me").status_code == 401


# ── Dashboard: clientes activos y creditos vencidos (6.2.2) ────────────────


def test_dashboard_cuenta_clientes_activos_y_creditos_vencidos(
    auth_client: TestClient, client_id: int
) -> None:
    terms = {
        "client_id": client_id,
        "amount": "100.00",
        "rate_type": "TEA",
        "annual_rate": "40.00",
        "start_date": "2026-08-01",  # vencido respecto de TODAY
        "term_days": 14,
        "installments_count": 2,
        "payment_frequency_days": 7,
    }
    assert auth_client.post("/api/credits", json=terms).status_code == 201
    body = auth_client.get("/api/dashboard").json()
    assert body["active_clients"] == 1
    assert body["overdue_credits"] == 1


# ── Integridad de la base (8.7) ────────────────────────────────────────────


def _raw_credit(client_id: int, **overrides) -> Credit:
    fields = dict(
        client_id=client_id,
        amount=Decimal("100.00"),
        start_date=date(2026, 9, 12),
        term_days=14,
        rate_type=RateType.TEA,
        annual_rate=Decimal("40.00"),
        periodic_rate=Decimal("0.006563965"),
        installments_count=2,
        payment_frequency_days=7,
        grace_type=GraceType.none,
        grace_days=0,
        total_interest=Decimal("1.00"),
        total_payment=Decimal("101.00"),
        outstanding_balance=Decimal("101.00"),
        status=CreditStatus.active,
    )
    return Credit(**(fields | overrides))


def _raw_client(session: Session) -> Client:
    client = Client(dni="40999888", first_name="Ana", last_name="Diaz")
    session.add(client)
    session.commit()
    return client


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": Decimal("200.01")},
        {"amount": Decimal("0.00")},
        {"term_days": 15},
        {"term_days": 0},
        {"installments_count": 0},
        {"payment_frequency_days": 0},
    ],
)
def test_la_base_rechaza_creditos_fuera_de_limites(session: Session, overrides: dict) -> None:
    client = _raw_client(session)
    session.add(_raw_credit(client.id, **overrides))
    with pytest.raises(IntegrityError):
        session.commit()


def test_la_base_acepta_el_monto_maximo_exacto(session: Session) -> None:
    client = _raw_client(session)
    session.add(_raw_credit(client.id, amount=Decimal("200.00")))
    session.commit()


def test_no_se_puede_borrar_un_cliente_con_creditos(session: Session) -> None:
    client = _raw_client(session)
    session.add(_raw_credit(client.id))
    session.commit()
    session.delete(client)
    with pytest.raises(IntegrityError):
        session.commit()


def test_el_pago_debe_cuadrar_con_su_imputacion(
    auth_client: TestClient, client_id: int, session: Session
) -> None:
    credit = auth_client.post(
        "/api/credits",
        json={
            "client_id": client_id,
            "amount": "100.00",
            "rate_type": "TEA",
            "annual_rate": "40.00",
            "start_date": TODAY.isoformat(),
            "term_days": 14,
            "installments_count": 2,
            "payment_frequency_days": 7,
        },
    ).json()
    installment_id = credit["installments"][0]["id"]
    session.add(
        Payment(
            credit_id=credit["id"],
            installment_id=installment_id,
            payment_date=TODAY,
            amount_received=Decimal("10.00"),
            late_interest_amount=Decimal("0.00"),
            compensatory_interest_amount=Decimal("1.00"),
            principal_amount=Decimal("8.00"),  # 9.00 != 10.00
            remaining_balance=Decimal("90.00"),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
