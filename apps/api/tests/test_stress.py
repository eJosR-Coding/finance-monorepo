"""Stress tests: the edges where a credit engine usually breaks.

Organised by the risk areas that matter for the defense: exact limits, rate
conversion, partial payments, late interest ordering, state transitions,
business rules, and database integrity.

Test names stay in Spanish - this output is academic evidence.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.enums import RateType
from app.core.errors import BusinessRuleError
from app.services import finance

START = date(2026, 9, 12)


def _terms(client_id: int, **overrides) -> dict:
    base = {
        "client_id": client_id,
        "amount": "140.00",
        "rate_type": "TEA",
        "annual_rate": "40.00",
        "start_date": START.isoformat(),
        "term_days": 14,
        "installments_count": 2,
        "payment_frequency_days": 7,
        "grace_type": "none",
        "grace_days": 0,
    }
    return base | overrides


def _schedule(**overrides) -> finance.Schedule:
    params = {
        "amount": Decimal("140.00"),
        "rate_type": RateType.TEA,
        "annual_rate": Decimal("40.00"),
        "start_date": START,
        "term_days": 14,
        "installments_count": 2,
        "payment_frequency_days": 7,
    }
    return finance.build_schedule(**(params | overrides))


# ══════════════════════════════════════════════════════════════════════════
# 1. Limites exactos del producto
# ══════════════════════════════════════════════════════════════════════════


def test_monto_exacto_de_200_con_plazo_de_14_dias_es_aceptado() -> None:
    """El limite superior es inclusivo: S/ 200.00 en 14 dias debe pasar."""
    schedule = _schedule(amount=Decimal("200.00"), term_days=14)
    assert schedule.amount == Decimal("200.00")
    assert schedule.final_balance == Decimal("0.00")


def test_un_centimo_por_encima_del_limite_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(amount=Decimal("200.01"))
    assert exc.value.code == "AMOUNT_ABOVE_MAX"


def test_monto_cero_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(amount=Decimal("0.00"))
    assert exc.value.code == "AMOUNT_NOT_POSITIVE"


def test_monto_negativo_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(amount=Decimal("-10.00"))
    assert exc.value.code == "AMOUNT_NOT_POSITIVE"


def test_plazo_de_15_dias_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(term_days=15, installments_count=1, payment_frequency_days=15)
    assert exc.value.code == "TERM_ABOVE_MAX"


def test_cero_cuotas_es_rechazado() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(installments_count=0)
    assert exc.value.code == "INSTALLMENTS_INVALID"


def test_frecuencia_incompatible_con_el_plazo_es_rechazada() -> None:
    """3 cuotas cada 7 dias son 21 dias: no caben en un plazo de 14."""
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(installments_count=3, payment_frequency_days=7)
    assert exc.value.code == "SCHEDULE_EXCEEDS_TERM"
    assert exc.value.details["last_day"] == 21


def test_frecuencia_cero_es_rechazada() -> None:
    with pytest.raises(BusinessRuleError) as exc:
        _schedule(payment_frequency_days=0)
    assert exc.value.code == "FREQUENCY_INVALID"


def test_una_sola_cuota_al_final_del_plazo() -> None:
    schedule = _schedule(installments_count=1, payment_frequency_days=14)
    assert len(schedule.rows) == 1
    assert schedule.rows[0].due_date == START + timedelta(days=14)
    assert schedule.rows[0].amortization_amount == Decimal("140.00")
    assert schedule.final_balance == Decimal("0.00")


def test_catorce_cuotas_diarias_dentro_del_plazo() -> None:
    """El caso mas fragmentado posible: una cuota por dia durante 14 dias."""
    schedule = _schedule(amount=Decimal("200.00"), installments_count=14, payment_frequency_days=1)
    assert len(schedule.rows) == 14
    assert schedule.final_balance == Decimal("0.00")
    assert sum(r.amortization_amount for r in schedule.rows) == Decimal("200.00")
    assert schedule.total_payment == Decimal("200.00") + schedule.total_interest


def test_tasa_altisima_pero_valida_sigue_cerrando_en_cero() -> None:
    schedule = _schedule(annual_rate=Decimal("500.00"))
    assert schedule.total_interest > 0
    assert schedule.final_balance == Decimal("0.00")


def test_monto_minimo_de_un_centimo() -> None:
    """S/ 0.01 en 2 cuotas: el redondeo no puede inventar ni perder plata."""
    schedule = _schedule(amount=Decimal("0.01"))
    assert sum(r.amortization_amount for r in schedule.rows) == Decimal("0.01")
    assert schedule.final_balance == Decimal("0.00")


# ══════════════════════════════════════════════════════════════════════════
# 2. Conversion de tasas
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("annual", "days", "expected"),
    [
        ("40.00", 7, "0.006563965"),
        ("40.00", 14, "0.013171015"),
        ("60.00", 7, "0.009180847"),
        ("60.00", 14, "0.018445982"),
    ],
)
def test_tea_a_periodica_para_7_y_14_dias(annual: str, days: int, expected: str) -> None:
    assert finance.periodic_rate(RateType.TEA, Decimal(annual), days) == Decimal(expected)


@pytest.mark.parametrize(
    ("annual", "days", "expected"),
    [
        ("36.00", 7, "0.007000000"),
        ("36.00", 14, "0.014000000"),
        ("40.00", 7, "0.007777778"),
    ],
)
def test_tna_a_periodica_es_proporcional(annual: str, days: int, expected: str) -> None:
    assert finance.periodic_rate(RateType.TNA, Decimal(annual), days) == Decimal(expected)


def test_la_tea_capitaliza_y_la_tna_no() -> None:
    """La TEA de 14 dias supera al doble de la de 7; la TNA es exactamente el doble.

    i_14 = (1 + i_7)^2 - 1 = 2·i_7 + i_7^2, asi que el interes compuesto suma
    ese termino cuadratico de mas. La TNA, al ser proporcional, no lo hace.
    """
    tea_7 = finance.periodic_rate(RateType.TEA, Decimal("40.00"), 7)
    tea_14 = finance.periodic_rate(RateType.TEA, Decimal("40.00"), 14)
    assert tea_14 > tea_7 * 2  # el termino cuadratico de la capitalizacion

    tna_7 = finance.periodic_rate(RateType.TNA, Decimal("40.00"), 7)
    tna_14 = finance.periodic_rate(RateType.TNA, Decimal("40.00"), 14)
    assert tna_14 == tna_7 * 2  # proporcional exacto


def test_encadenar_dos_periodos_de_7_dias_equivale_al_de_14() -> None:
    """Coherencia interna: (1 + i_7)^2 - 1 debe dar i_14 salvo el redondeo a 9 dp."""
    tea_7 = finance.periodic_rate(RateType.TEA, Decimal("40.00"), 7)
    tea_14 = finance.periodic_rate(RateType.TEA, Decimal("40.00"), 14)
    chained = (Decimal(1) + tea_7) ** 2 - Decimal(1)
    assert abs(chained - tea_14) <= Decimal("0.000000010")


@pytest.mark.parametrize("annual", ["0.00", "12.00", "40.00", "60.00", "120.00"])
@pytest.mark.parametrize("installments", [1, 2, 7, 14])
def test_el_valor_presente_del_cronograma_es_el_capital(annual: str, installments: int) -> None:
    """Verificacion independiente de la formula.

    En vez de recalcular la cuota con la misma formula, comprobamos la propiedad
    que define al metodo frances: descontadas al tipo periodico, las cuotas
    valen hoy exactamente el capital prestado. La tolerancia es de un centimo
    por cuota, que es el redondeo acumulado.
    """
    schedule = _schedule(
        amount=Decimal("200.00"),
        annual_rate=Decimal(annual),
        installments_count=installments,
        payment_frequency_days=14 // installments,
    )
    rate = schedule.periodic_rate
    present_value = sum(
        row.installment_amount / (Decimal(1) + rate) ** period
        for period, row in enumerate(schedule.rows, start=1)
    )
    assert abs(present_value - Decimal("200.00")) <= Decimal("0.01") * installments


# ══════════════════════════════════════════════════════════════════════════
# 3. Pagos parciales
# ══════════════════════════════════════════════════════════════════════════


def _credit(auth_client: TestClient, client_id: int, **overrides) -> dict:
    response = auth_client.post("/api/credits", json=_terms(client_id, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_varios_pagos_parciales_saldan_la_cuota_sin_perder_centimos(
    auth_client: TestClient, client_id: int
) -> None:
    """Tres abonos de S/ 20 + S/ 30 + el resto deben cerrar la cuota en 0.00."""
    credit = _credit(auth_client, client_id)
    credit_id = credit["id"]

    for amount in ("20.00", "30.00"):
        response = auth_client.post(
            f"/api/credits/{credit_id}/payments",
            json={"amount_received": amount, "payment_date": START.isoformat()},
        )
        assert response.status_code == 201, response.text

    detail = auth_client.get(f"/api/credits/{credit_id}").json()
    first = detail["installments"][0]
    assert first["status"] == "pending"
    assert first["paid_amount"] == "50.00"
    assert first["outstanding_amount"] == "20.69"

    # El remate exacto de lo que falta.
    result = auth_client.post(
        f"/api/credits/{credit_id}/payments",
        json={"amount_received": "20.69", "payment_date": START.isoformat()},
    ).json()

    detail = auth_client.get(f"/api/credits/{credit_id}").json()
    first = detail["installments"][0]
    assert first["status"] == "paid"
    assert first["outstanding_amount"] == "0.00"
    assert first["paid_amount"] == first["installment_amount"]
    assert result["remaining_balance"] == "70.69"


def test_la_suma_de_los_pagos_iguala_el_total_a_pagar(
    auth_client: TestClient, client_id: int
) -> None:
    """Pagando de a poco hasta cancelar, no se cobra ni un centimo de mas."""
    credit = _credit(auth_client, client_id)
    credit_id = credit["id"]
    total = Decimal(credit["total_payment"])

    collected = Decimal("0.00")
    for _ in range(20):
        detail = auth_client.get(f"/api/credits/{credit_id}").json()
        if detail["status"] == "paid":
            break
        pending = Decimal(detail["outstanding_balance"])
        chunk = min(Decimal("15.00"), pending)
        response = auth_client.post(
            f"/api/credits/{credit_id}/payments",
            json={
                "amount_received": str(chunk),
                "payment_date": START.isoformat(),
                # Abonos iguales uno tras otro en milisegundos: para el guarda de
                # duplicados esto es un reenvio, asi que se confirma a proposito.
                "allow_duplicate": True,
            },
        )
        assert response.status_code == 201, response.text
        collected += chunk

    assert collected == total
    detail = auth_client.get(f"/api/credits/{credit_id}").json()
    assert detail["status"] == "paid"
    assert detail["outstanding_balance"] == "0.00"
    assert all(i["outstanding_amount"] == "0.00" for i in detail["installments"])


def test_pagar_un_centimo_de_mas_es_rechazado(auth_client: TestClient, client_id: int) -> None:
    credit = _credit(auth_client, client_id)
    response = auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "141.39", "payment_date": START.isoformat()},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "PAYMENT_EXCEEDS_DEBT"
    assert response.json()["details"]["max_amount"] == "141.38"


def test_pago_de_cero_es_rechazado(auth_client: TestClient, client_id: int) -> None:
    credit = _credit(auth_client, client_id)
    response = auth_client.post(
        f"/api/credits/{credit['id']}/payments", json={"amount_received": "0.00"}
    )
    assert response.status_code == 422


def test_no_se_puede_pagar_un_credito_ya_cancelado(
    auth_client: TestClient, client_id: int
) -> None:
    credit = _credit(auth_client, client_id)
    auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "141.38", "payment_date": START.isoformat()},
    )
    response = auth_client.post(
        f"/api/credits/{credit['id']}/payments", json={"amount_received": "10.00"}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CREDIT_ALREADY_PAID"


# ══════════════════════════════════════════════════════════════════════════
# 4. Mora
# ══════════════════════════════════════════════════════════════════════════


def _overdue_credit(auth_client: TestClient, client_id: int, days_ago: int) -> dict:
    start = (date.today() - timedelta(days=days_ago)).isoformat()
    return _credit(auth_client, client_id, start_date=start)


def test_pagar_el_mismo_dia_del_vencimiento_no_genera_mora(
    auth_client: TestClient, client_id: int
) -> None:
    """Vence hoy: todavia esta al dia, la mora debe ser 0.00."""
    credit = _overdue_credit(auth_client, client_id, days_ago=7)
    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    first = detail["installments"][0]
    assert first["due_date"] == date.today().isoformat()
    assert first["days_late"] == 0

    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview",
        json={"amount_received": first["installment_amount"]},
    ).json()
    assert preview["late_interest_amount"] == "0.00"
    assert preview["outcome"] == "exact"


def test_un_dia_de_atraso_ya_genera_mora(auth_client: TestClient, client_id: int) -> None:
    credit = _overdue_credit(auth_client, client_id, days_ago=8)
    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["installments"][0]["days_late"] == 1

    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview", json={"amount_received": "100.00"}
    ).json()
    assert Decimal(preview["late_interest_amount"]) > 0


def test_la_mora_crece_con_los_dias(auth_client: TestClient) -> None:
    """Mismo saldo, mas dias de atraso, mas mora."""
    base = Decimal("70.69")
    moras = [finance.late_interest(base, days) for days in (1, 3, 7, 15, 30)]
    assert moras == sorted(moras)
    assert moras[0] > 0
    assert moras[-1] == finance.late_interest(base, 30)


def test_el_pago_cubre_primero_la_mora_luego_interes_y_al_final_capital(
    auth_client: TestClient, client_id: int
) -> None:
    """Un pago chico sobre una cuota vencida no debe tocar el capital."""
    credit = _overdue_credit(auth_client, client_id, days_ago=20)
    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview", json={"amount_received": "1.00"}
    ).json()

    mora = Decimal(preview["late_interest_amount"])
    interes = Decimal(preview["compensatory_interest_amount"])
    capital = Decimal(preview["principal_amount"])

    assert mora > 0, "una cuota vencida hace 13 dias debe devengar mora"
    assert mora + interes + capital == Decimal("1.00")
    # El orden es estricto: solo hay capital si mora e interes ya estan cubiertos.
    if capital > 0:
        assert interes == Decimal(
            [i for i in auth_client.get(f"/api/credits/{credit['id']}").json()["installments"]][0][
                "interest_amount"
            ]
        )


def test_la_mora_no_reduce_el_saldo_del_credito(
    auth_client: TestClient, client_id: int
) -> None:
    """La mora es un cargo extra: se cobra, pero no amortiza el cronograma."""
    credit = _overdue_credit(auth_client, client_id, days_ago=20)
    before = Decimal(auth_client.get(f"/api/credits/{credit['id']}").json()["outstanding_balance"])

    result = auth_client.post(
        f"/api/credits/{credit['id']}/payments", json={"amount_received": "30.00"}
    ).json()

    mora = Decimal(result["late_interest_amount"])
    aplicado_a_cuotas = Decimal(result["compensatory_interest_amount"]) + Decimal(
        result["principal_amount"]
    )
    assert mora > 0
    assert Decimal(result["remaining_balance"]) == before - aplicado_a_cuotas


# ══════════════════════════════════════════════════════════════════════════
# 5. Transiciones de estado
# ══════════════════════════════════════════════════════════════════════════


def test_la_cuota_recorre_pendiente_vencida_y_pagada(
    auth_client: TestClient, client_id: int
) -> None:
    # Pendiente: vence en el futuro.
    future = _credit(auth_client, client_id, start_date=date.today().isoformat())
    assert auth_client.get(f"/api/credits/{future['id']}").json()["installments"][0][
        "status"
    ] == "pending"

    # Vencida: la fecha ya paso.
    overdue = _overdue_credit(auth_client, client_id, days_ago=20)
    detail = auth_client.get(f"/api/credits/{overdue['id']}").json()
    assert detail["installments"][0]["status"] == "overdue"
    assert detail["status"] == "overdue"

    # Pagada: se cancela lo exigible.
    preview = auth_client.post(
        f"/api/credits/{overdue['id']}/payments/preview", json={"amount_received": "500.00"}
    ).json()
    auth_client.post(
        f"/api/credits/{overdue['id']}/payments",
        json={"amount_received": preview["total_applied"]},
    )
    detail = auth_client.get(f"/api/credits/{overdue['id']}").json()
    assert detail["status"] == "paid"
    assert all(i["status"] == "paid" for i in detail["installments"])
    assert detail["outstanding_balance"] == "0.00"


def test_el_cliente_se_bloquea_y_se_desbloquea_solo(
    auth_client: TestClient, client_id: int
) -> None:
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "enabled"

    credit = _overdue_credit(auth_client, client_id, days_ago=20)
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "blocked"

    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview", json={"amount_received": "500.00"}
    ).json()
    auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": preview["total_applied"]},
    )
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "enabled"


def test_pagar_solo_la_cuota_vencida_desbloquea_aunque_queden_cuotas_futuras(
    auth_client: TestClient, client_id: int
) -> None:
    """Regularizar lo vencido basta: las cuotas que aun no vencen no bloquean."""
    credit = _overdue_credit(auth_client, client_id, days_ago=8)  # cuota 1 vencida, cuota 2 no
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "blocked"

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    first = detail["installments"][0]
    preview = auth_client.post(
        f"/api/credits/{credit['id']}/payments/preview",
        json={"amount_received": "500.00", "installment_id": first["id"]},
    ).json()
    due_for_first = (
        Decimal(preview["allocations"][0]["late_interest_amount"])
        + Decimal(preview["allocations"][0]["compensatory_interest_amount"])
        + Decimal(preview["allocations"][0]["principal_amount"])
    )
    auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": str(due_for_first), "installment_id": first["id"]},
    )

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["installments"][0]["status"] == "paid"
    assert detail["installments"][1]["status"] == "pending"
    assert detail["status"] == "active"
    assert auth_client.get(f"/api/clients/{client_id}").json()["credit_status"] == "enabled"


# ══════════════════════════════════════════════════════════════════════════
# 6. Reglas de negocio via API
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"amount": "200.01"}, "AMOUNT_ABOVE_MAX"),
        ({"amount": "0.00"}, "VALIDATION_ERROR"),
        ({"term_days": 15}, "TERM_ABOVE_MAX"),
        ({"installments_count": 0}, "VALIDATION_ERROR"),
        ({"installments_count": 3, "payment_frequency_days": 7}, "SCHEDULE_EXCEEDS_TERM"),
        ({"payment_frequency_days": 0}, "VALIDATION_ERROR"),
        ({"annual_rate": "-5.00"}, "VALIDATION_ERROR"),
        ({"grace_type": "partial", "grace_days": 0}, "GRACE_INVALID"),
    ],
)
def test_la_api_rechaza_condiciones_invalidas(
    auth_client: TestClient, client_id: int, overrides: dict, expected_code: str
) -> None:
    response = auth_client.post("/api/credits", json=_terms(client_id, **overrides))
    assert response.status_code == 422, response.text
    assert response.json()["code"] == expected_code
    # Y sobre todo: no quedo nada guardado.
    assert auth_client.get("/api/credits").json()["total"] == 0


def test_un_credito_rechazado_no_deja_cuotas_huerfanas(
    auth_client: TestClient, client_id: int, session
) -> None:
    """Rollback real: ni credito ni cuotas en la base."""
    from sqlalchemy import func, select

    from app.models import Credit, Installment

    auth_client.post("/api/credits", json=_terms(client_id, amount="500.00"))
    assert session.scalar(select(func.count()).select_from(Credit)) == 0
    assert session.scalar(select(func.count()).select_from(Installment)) == 0


def test_credito_a_cliente_inexistente_devuelve_404(auth_client: TestClient) -> None:
    response = auth_client.post("/api/credits", json=_terms(99999))
    assert response.status_code == 404
    assert response.json()["code"] == "CLIENT_NOT_FOUND"


def test_pago_a_credito_inexistente_devuelve_404(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/credits/99999/payments", json={"amount_received": "10.00"}
    )
    assert response.status_code == 404
    assert response.json()["code"] == "CREDIT_NOT_FOUND"


def test_detalle_de_credito_inexistente_devuelve_404(auth_client: TestClient) -> None:
    assert auth_client.get("/api/credits/99999").status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# 7. Integridad de la base
# ══════════════════════════════════════════════════════════════════════════


def test_crear_un_credito_crea_exactamente_sus_cuotas(
    auth_client: TestClient, client_id: int, session
) -> None:
    from sqlalchemy import func, select

    from app.models import Installment

    for count, frequency in [(1, 14), (2, 7), (7, 2), (14, 1)]:
        auth_client.post(
            "/api/credits",
            json=_terms(client_id, installments_count=count, payment_frequency_days=frequency),
        )

    credits = auth_client.get("/api/credits").json()["items"]
    assert len(credits) == 4
    for credit in credits:
        stored = session.scalar(
            select(func.count())
            .select_from(Installment)
            .where(Installment.credit_id == credit["id"])
        )
        assert stored == credit["installments_count"]


def test_los_pagos_no_se_cruzan_entre_creditos(
    auth_client: TestClient, client_id: int
) -> None:
    """Pagar el credito A no puede tocar el credito B."""
    first = _credit(auth_client, client_id)
    second = _credit(auth_client, client_id, amount="100.00")

    auth_client.post(
        f"/api/credits/{first['id']}/payments",
        json={"amount_received": "70.69", "payment_date": START.isoformat()},
    )

    assert len(auth_client.get(f"/api/credits/{first['id']}/payments").json()) == 1
    assert auth_client.get(f"/api/credits/{second['id']}/payments").json() == []

    detail_second = auth_client.get(f"/api/credits/{second['id']}").json()
    assert detail_second["outstanding_balance"] == second["total_payment"]
    assert all(i["status"] == "pending" for i in detail_second["installments"])


def test_los_datos_sobreviven_a_recargar(auth_client: TestClient, client_id: int) -> None:
    """Equivalente a refrescar la pagina: pedir todo de nuevo devuelve lo mismo."""
    credit = _credit(auth_client, client_id)
    auth_client.post(
        f"/api/credits/{credit['id']}/payments",
        json={"amount_received": "70.69", "payment_date": START.isoformat()},
    )

    first_read = auth_client.get(f"/api/credits/{credit['id']}").json()
    second_read = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert first_read == second_read
    assert first_read["installments"][0]["status"] == "paid"


def test_dni_duplicado_no_crea_un_segundo_cliente(
    auth_client: TestClient, client_id: int
) -> None:
    before = auth_client.get("/api/clients").json()["total"]
    payload = {
        "dni": "71456238",
        "first_name": "Otra",
        "last_name": "Persona",
        "phone": "900 000 000",
        "address": "Otra direccion",
    }
    assert auth_client.post("/api/clients", json=payload).status_code == 409
    assert auth_client.get("/api/clients").json()["total"] == before


# ══════════════════════════════════════════════════════════════════════════
# 8. Idempotencia y reenvios accidentales
# ══════════════════════════════════════════════════════════════════════════


def test_reenviar_el_mismo_credito_no_crea_un_duplicado(
    auth_client: TestClient, client_id: int
) -> None:
    first = auth_client.post("/api/credits", json=_terms(client_id))
    second = auth_client.post("/api/credits", json=_terms(client_id))

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "DUPLICATE_CREDIT"
    assert second.json()["details"]["credit_code"] == "CR-0001"
    assert auth_client.get("/api/credits").json()["total"] == 1


def test_se_puede_otorgar_un_credito_identico_confirmando(
    auth_client: TestClient, client_id: int
) -> None:
    """El bodeguero manda: si de verdad son dos creditos, se registran."""
    auth_client.post("/api/credits", json=_terms(client_id))
    second = auth_client.post("/api/credits", json=_terms(client_id, allow_duplicate=True))

    assert second.status_code == 201
    assert auth_client.get("/api/credits").json()["total"] == 2


def test_condiciones_distintas_no_cuentan_como_duplicado(
    auth_client: TestClient, client_id: int
) -> None:
    auth_client.post("/api/credits", json=_terms(client_id))
    other = auth_client.post("/api/credits", json=_terms(client_id, amount="100.00"))

    assert other.status_code == 201
    assert auth_client.get("/api/credits").json()["total"] == 2


def test_reenviar_el_mismo_pago_no_cobra_dos_veces(
    auth_client: TestClient, client_id: int
) -> None:
    """El bug caro: sin esta guarda el credito quedaba pagado sin recibir la plata."""
    credit = _credit(auth_client, client_id)
    payment = {
        "amount_received": "70.69",
        "payment_date": START.isoformat(),
        "payment_method": "cash",
    }

    first = auth_client.post(f"/api/credits/{credit['id']}/payments", json=payment)
    second = auth_client.post(f"/api/credits/{credit['id']}/payments", json=payment)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "DUPLICATE_PAYMENT"

    payments = auth_client.get(f"/api/credits/{credit['id']}/payments").json()
    assert len(payments) == 1

    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["outstanding_balance"] == "70.69"
    assert detail["status"] == "active"
    assert detail["installments"][1]["status"] == "pending"


def test_se_puede_registrar_un_pago_identico_confirmando(
    auth_client: TestClient, client_id: int
) -> None:
    """Un cliente si puede pagar dos veces el mismo monto el mismo dia."""
    credit = _credit(auth_client, client_id)
    payment = {
        "amount_received": "70.69",
        "payment_date": START.isoformat(),
        "payment_method": "cash",
    }

    auth_client.post(f"/api/credits/{credit['id']}/payments", json=payment)
    second = auth_client.post(
        f"/api/credits/{credit['id']}/payments", json=payment | {"allow_duplicate": True}
    )

    assert second.status_code == 201
    assert len(auth_client.get(f"/api/credits/{credit['id']}/payments").json()) == 2
    detail = auth_client.get(f"/api/credits/{credit['id']}").json()
    assert detail["status"] == "paid"


def test_montos_distintos_no_cuentan_como_pago_duplicado(
    auth_client: TestClient, client_id: int
) -> None:
    credit = _credit(auth_client, client_id)
    base = {"payment_date": START.isoformat(), "payment_method": "cash"}

    assert (
        auth_client.post(
            f"/api/credits/{credit['id']}/payments", json=base | {"amount_received": "20.00"}
        ).status_code
        == 201
    )
    assert (
        auth_client.post(
            f"/api/credits/{credit['id']}/payments", json=base | {"amount_received": "30.00"}
        ).status_code
        == 201
    )
    assert len(auth_client.get(f"/api/credits/{credit['id']}/payments").json()) == 2


def test_las_lecturas_y_la_simulacion_son_idempotentes(
    auth_client: TestClient, client_id: int
) -> None:
    """GET, simulate y preview no pueden dejar rastro por mucho que se repitan."""
    credit = _credit(auth_client, client_id)

    for _ in range(3):
        assert auth_client.get(f"/api/credits/{credit['id']}").json() == auth_client.get(
            f"/api/credits/{credit['id']}"
        ).json()
        auth_client.post("/api/credits/simulate", json=_terms(client_id))
        auth_client.post(
            f"/api/credits/{credit['id']}/payments/preview", json={"amount_received": "70.69"}
        )

    assert auth_client.get("/api/credits").json()["total"] == 1
    assert auth_client.get(f"/api/credits/{credit['id']}/payments").json() == []


def test_actualizar_al_cliente_dos_veces_da_el_mismo_resultado(
    auth_client: TestClient, client_id: int
) -> None:
    payload = {"phone": "999 888 777"}
    first = auth_client.patch(f"/api/clients/{client_id}", json=payload).json()
    second = auth_client.patch(f"/api/clients/{client_id}", json=payload).json()

    assert first["phone"] == second["phone"] == "999 888 777"
    assert auth_client.get("/api/clients").json()["total"] == 1
