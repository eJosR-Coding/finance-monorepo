"""End-to-end API tests: the exact demo flow the assignment asks for.

Test names stay in Spanish - the pytest run is academic evidence (Anexo F).
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD

START = "2026-09-12"


def _terms(client_id: int, **overrides) -> dict:
    base = {
        "client_id": client_id,
        "amount": "140.00",
        "rate_type": "TEA",
        "annual_rate": "40.00",
        "start_date": START,
        "term_days": 14,
        "installments_count": 2,
        "payment_frequency_days": 7,
        "grace_type": "none",
        "grace_days": 0,
    }
    return base | overrides


# ── Autenticacion ──────────────────────────────────────────────────────────


def test_login_con_credenciales_validas_devuelve_token(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ADMIN_EMAIL
    assert "password_hash" not in body["user"]


def test_login_con_contrasenia_incorrecta_es_rechazado(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "incorrecta"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_endpoints_protegidos_exigen_token(client: TestClient) -> None:
    assert client.get("/api/clients").status_code == 401
    assert client.get("/api/dashboard").status_code == 401


def test_me_devuelve_al_administrador(auth_client: TestClient) -> None:
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_EMAIL


# ── Clientes ───────────────────────────────────────────────────────────────


def test_registrar_cliente_lo_deja_habilitado(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/clients",
        json={
            "dni": "70128455",
            "first_name": "Luis",
            "last_name": "Herrera",
            "phone": "965 118 920",
            "address": "Jr. Union 120, Lima",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["credit_status"] == "enabled"
    assert body["full_name"] == "Luis Herrera"
    assert body["initials"] == "LH"


def test_dni_duplicado_es_rechazado(auth_client: TestClient, client_id: int) -> None:
    response = auth_client.post(
        "/api/clients",
        json={
            "dni": "71456238",
            "first_name": "Otra",
            "last_name": "Persona",
            "phone": "900 000 000",
            "address": "Otra direccion",
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "DNI_ALREADY_EXISTS"


def test_dni_no_numerico_es_rechazado(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/clients",
        json={
            "dni": "ABC12345",
            "first_name": "Test",
            "last_name": "Test",
            "phone": "900 000 000",
            "address": "Direccion",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_buscar_clientes_por_nombre_y_dni(auth_client: TestClient, client_id: int) -> None:
    assert auth_client.get("/api/clients", params={"search": "maria"}).json()["total"] == 1
    assert auth_client.get("/api/clients", params={"search": "71456"}).json()["total"] == 1
    assert auth_client.get("/api/clients", params={"search": "zzz"}).json()["total"] == 0


# ── Simulacion ─────────────────────────────────────────────────────────────


def test_simular_credito_devuelve_el_cronograma_frances(
    auth_client: TestClient, client_id: int
) -> None:
    response = auth_client.post("/api/credits/simulate", json=_terms(client_id))
    assert response.status_code == 200
    body = response.json()

    assert body["periodic_rate"] == "0.006563965"
    assert body["periodic_rate_percent"] == "0.6563965"
    assert body["installment_amount"] == "70.69"
    assert body["total_interest"] == "1.38"
    assert body["total_payment"] == "141.38"
    assert body["final_balance"] == "0.00"
    assert body["tcea"] == "40.00"

    schedule = body["schedule"]
    assert len(schedule) == 2
    assert schedule[0] == {
        "installment_number": 1,
        "due_date": "2026-09-19",
        "opening_balance": "140.00",
        "interest": "0.92",
        "amortization": "69.77",
        "installment": "70.69",
        "closing_balance": "70.23",
    }
    assert schedule[1]["closing_balance"] == "0.00"


def test_simular_no_guarda_nada(auth_client: TestClient, client_id: int) -> None:
    auth_client.post("/api/credits/simulate", json=_terms(client_id))
    assert auth_client.get("/api/credits").json()["total"] == 0


def test_simular_monto_mayor_al_maximo_es_rechazado(
    auth_client: TestClient, client_id: int
) -> None:
    response = auth_client.post(
        "/api/credits/simulate", json=_terms(client_id, amount="250.00")
    )
    assert response.status_code == 422
    assert response.json()["code"] == "AMOUNT_ABOVE_MAX"


def test_simular_plazo_mayor_al_maximo_es_rechazado(
    auth_client: TestClient, client_id: int
) -> None:
    response = auth_client.post("/api/credits/simulate", json=_terms(client_id, term_days=20))
    assert response.status_code == 422
    assert response.json()["code"] == "TERM_ABOVE_MAX"


# ── Otorgamiento ───────────────────────────────────────────────────────────


def test_crear_credito_persiste_las_cuotas(auth_client: TestClient, client_id: int) -> None:
    response = auth_client.post("/api/credits", json=_terms(client_id))
    assert response.status_code == 201
    credit = response.json()

    assert credit["code"] == "CR-0001"
    assert credit["status"] == "active"
    assert credit["outstanding_balance"] == "141.38"
    assert len(credit["installments"]) == 2
    assert credit["installments"][0]["status"] == "pending"
    assert credit["installments"][-1]["closing_balance"] == "0.00"

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["installments"] == credit["installments"]


def test_crear_credito_para_cliente_inexistente_devuelve_404(auth_client: TestClient) -> None:
    response = auth_client.post("/api/credits", json=_terms(9999))
    assert response.status_code == 404
    assert response.json()["code"] == "CLIENT_NOT_FOUND"


def test_credito_con_monto_sobre_el_limite_no_se_guarda(
    auth_client: TestClient, client_id: int
) -> None:
    response = auth_client.post("/api/credits", json=_terms(client_id, amount="200.01"))
    assert response.status_code == 422
    assert auth_client.get("/api/credits").json()["total"] == 0


# ── Pagos ──────────────────────────────────────────────────────────────────


def test_pago_exacto_se_reparte_en_interes_y_capital(
    auth_client: TestClient, client_id: int
) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()

    response = auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "70.69", "payment_method": "yape", "payment_date": START},
    )
    assert response.status_code == 201
    result = response.json()

    assert result["late_interest_amount"] == "0.00"
    assert result["compensatory_interest_amount"] == "0.92"
    assert result["principal_amount"] == "69.77"
    assert result["remaining_balance"] == "70.69"
    assert result["credit_status"] == "active"
    assert result["allocations"][0]["installment_number"] == 1

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["installments"][0]["status"] == "paid"
    assert detail["installments"][1]["status"] == "pending"


def test_pago_parcial_deja_la_cuota_pendiente(auth_client: TestClient, client_id: int) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()

    result = auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "30.00", "payment_date": START},
    ).json()

    # Waterfall: interest first, whatever is left goes to principal.
    assert result["compensatory_interest_amount"] == "0.92"
    assert result["principal_amount"] == "29.08"
    assert result["remaining_balance"] == "111.38"

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["installments"][0]["status"] == "pending"
    assert detail["installments"][0]["outstanding_amount"] == "40.69"


def test_cancelar_el_credito_lo_marca_como_pagado(
    auth_client: TestClient, client_id: int
) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()
    result = auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "141.38", "payment_date": START},
    ).json()

    assert result["remaining_balance"] == "0.00"
    assert result["credit_status"] == "paid"
    assert len(result["allocations"]) == 2

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert all(i["status"] == "paid" for i in detail["installments"])


def test_pago_mayor_a_la_deuda_es_rechazado(auth_client: TestClient, client_id: int) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()
    response = auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "500.00", "payment_date": START},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "PAYMENT_EXCEEDS_DEBT"
    assert body["details"]["max_amount"] == "141.38"


def test_preview_no_registra_el_pago(auth_client: TestClient, client_id: int) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()
    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview",
        json={"amount_received": "70.69", "payment_date": START},
    ).json()

    assert preview["outcome"] == "exact"
    assert preview["compensatory_interest_amount"] == "0.92"
    assert preview["principal_amount"] == "69.77"
    assert auth_client.get(f"/api/credits/{credit['id']}/payments").json() == []


def test_historial_de_pagos_del_credito(auth_client: TestClient, client_id: int) -> None:
    credit = auth_client.post("/api/credits", json=_terms(client_id)).json()
    auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "70.69", "payment_date": START},
    )
    payments = auth_client.get(f"/api/credits/{credit['id']}/payments").json()
    assert len(payments) == 1
    assert payments[0]["payment_method"] == "cash"
    assert payments[0]["remaining_balance"] == "70.69"


# ── Mora y bloqueo ─────────────────────────────────────────────────────────


def _overdue_credit(auth_client: TestClient, client_id: int) -> dict:
    """Grant a credit whose installments are already past due today."""
    start = (date.today() - timedelta(days=20)).isoformat()
    return auth_client.post("/api/credits", json=_terms(client_id, start_date=start)).json()


def test_cuota_vencida_bloquea_al_cliente(auth_client: TestClient, client_id: int) -> None:
    _overdue_credit(auth_client, client_id)

    detail = auth_client.get(f"/api/clients/{client_id}").json()
    assert detail["credit_status"] == "blocked"

    overdue = auth_client.get("/api/overdue").json()
    assert overdue["blocked_clients"] == 1
    assert overdue["overdue_installments"] == 2
    assert overdue["rows"][0]["days_late"] > 0


def test_cliente_bloqueado_no_puede_recibir_otro_credito(
    auth_client: TestClient, client_id: int
) -> None:
    _overdue_credit(auth_client, client_id)

    response = auth_client.post("/api/credits", json=_terms(client_id))
    assert response.status_code == 422
    body = response.json()
    assert body["code"] in {"CLIENT_BLOCKED", "CLIENT_HAS_OVERDUE_DEBT"}
    assert "deuda vencida" in body["message"]


def test_regularizar_la_deuda_habilita_al_cliente(
    auth_client: TestClient, client_id: int
) -> None:
    credit = _overdue_credit(auth_client, client_id)
    detail = auth_client.get(f"/api/credits/{credit['id']}").json()

    # Pay everything owed, late interest included.
    total_due = sum(
        float(i["outstanding_amount"]) for i in detail["installments"]
    )
    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview",
        json={"amount_received": f"{total_due + 50:.2f}"},
    ).json()
    exact = preview["total_applied"]

    result = auth_client.post(
        f"/api/credits/{credit['id']}/payments", json={"amount_received": exact}
    ).json()

    assert float(result["late_interest_amount"]) > 0
    assert result["credit_status"] == "paid"
    assert result["client_credit_status"] == "enabled"
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "enabled"


def test_no_se_puede_habilitar_a_mano_a_un_cliente_con_deuda_vencida(
    auth_client: TestClient, client_id: int
) -> None:
    _overdue_credit(auth_client, client_id)
    response = auth_client.patch(
        f"/api/clients/{client_id}", json={"credit_status": "enabled"}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CLIENT_HAS_OVERDUE_DEBT"


# ── Dashboard y parametros ─────────────────────────────────────────────────


def test_dashboard_resume_el_negocio(auth_client: TestClient, client_id: int) -> None:
    auth_client.post("/api/credits", json=_terms(client_id, start_date=date.today().isoformat()))

    body = auth_client.get("/api/dashboard").json()
    assert body["active_credits"] == 1
    assert body["outstanding_total"] == "141.38"
    assert body["blocked_clients"] == 0
    assert len(body["upcoming_installments"]) == 2
    assert len(body["recent_credits"]) == 1
    assert body["recent_credits"][0]["credit_code"] == "CR-0001"


def test_config_expone_los_limites_del_producto(client: TestClient) -> None:
    body = client.get("/api/config").json()
    assert body["max_credit_amount"] == "200.00"
    assert body["max_term_days"] == 14
    assert body["days_per_year"] == 360
    assert body["currency"] == "PEN"
    assert body["late_monthly_rate_percent"] == "2.00"


def test_detalle_del_cliente_trae_creditos_pagos_e_historial(
    auth_client: TestClient, client_id: int
) -> None:
    credit = auth_client.post(
        "/api/credits", json=_terms(client_id, start_date=date.today().isoformat())
    ).json()
    auth_client.post(
        f"/api/credits/{credit['id']}/payments", json={"amount_received": "70.69"}
    )

    detail = auth_client.get(f"/api/clients/{client_id}").json()
    assert detail["active_credits"] == 1
    assert detail["outstanding_balance"] == "70.69"
    assert detail["total_paid"] == "70.69"
    assert len(detail["credits"]) == 1
    assert len(detail["payments"]) == 1
    assert [item["type"] for item in detail["activity"]][-1] == "client_created"
