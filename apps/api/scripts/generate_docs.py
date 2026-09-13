"""Generate the academic annexes from the implementation itself.

Anexo C (test-cases.md) and Anexo F (validation.md) are written from the real
engine output, never typed by hand. If the engine changes, the documents change
with it - that's the whole point, no drifting tables.

Run it with:  uv run python scripts/generate_docs.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import Date, DateTime, Integer, String  # noqa: E402
from sqlalchemy import Enum as SAEnum

from app.core.config import BASE_DIR, settings  # noqa: E402
from app.core.types import DecimalText  # noqa: E402
from app.database import Base  # noqa: E402
from app.services.finance import Schedule, build_schedule  # noqa: E402
from scripts.academic_cases import ACADEMIC_CASES, AcademicCase  # noqa: E402

DOCS_DIR = BASE_DIR.parent.parent / "docs"
GENERATED_NOTE = (
    "> Documento generado automaticamente por `apps/api/scripts/generate_docs.py`.\n"
    "> No lo edites a mano: su contenido se lee del sistema real.\n"
)


def run_case(case: AcademicCase) -> Schedule:
    return build_schedule(
        amount=case.amount,
        rate_type=case.rate_type,
        annual_rate=case.annual_rate,
        start_date=case.start_date,
        term_days=case.term_days,
        installments_count=case.installments_count,
        payment_frequency_days=case.payment_frequency_days,
    )


def money(value: Decimal) -> str:
    return f"S/ {value:,.2f}"


# ══════════════════════════════════════════════════════════════════════════
# Anexo C - cronogramas completos
# ══════════════════════════════════════════════════════════════════════════


def schedule_section(case: AcademicCase, schedule: Schedule) -> str:
    lines: list[str] = []
    lines.append(f"## {case.title}\n")

    lines.append("### Datos iniciales\n")
    lines.append("| Variable | Valor |")
    lines.append("| --- | --- |")
    lines.append(f"| Capital (P) | {money(case.amount)} |")
    lines.append(f"| Tipo de tasa | {case.rate_type.value} |")
    lines.append(f"| Tasa anual | {case.annual_rate} % |")
    lines.append(f"| Fecha de inicio | {case.start_date.strftime('%d/%m/%Y')} |")
    lines.append(f"| Plazo | {case.term_days} dias |")
    lines.append(f"| Numero de cuotas (n) | {case.installments_count} |")
    lines.append(f"| Frecuencia de pago | cada {case.payment_frequency_days} dias |")
    lines.append("| Periodo de gracia | Sin gracia |")
    lines.append(f"| Base anual | {settings.days_per_year} dias |\n")

    lines.append("### Conversion de la tasa\n")
    lines.append("```")
    lines.append("i_d = (1 + TEA)^(d / 360) - 1")
    lines.append(
        f"i_{case.payment_frequency_days} = (1 + {case.annual_rate / 100})"
        f"^({case.payment_frequency_days} / {settings.days_per_year}) - 1"
    )
    lines.append(f"i_{case.payment_frequency_days} = {schedule.periodic_rate}")
    lines.append(f"i_{case.payment_frequency_days} = {schedule.periodic_rate_percent} %")
    lines.append("```\n")

    lines.append("### Cuota (metodo frances)\n")
    lines.append("```")
    lines.append("C = P * [ i (1+i)^n ] / [ (1+i)^n - 1 ]")
    lines.append(
        f"C = {case.amount} * [ {schedule.periodic_rate} "
        f"(1+{schedule.periodic_rate})^{case.installments_count} ] / "
        f"[ (1+{schedule.periodic_rate})^{case.installments_count} - 1 ]"
    )
    lines.append(f"C = {schedule.installment_amount}")
    lines.append("```\n")

    lines.append("### Cronograma de amortizacion\n")
    lines.append(
        "| # | Fecha | Saldo inicial | Interes | Amortizacion | Cuota | Saldo final |"
    )
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: |")
    for row in schedule.rows:
        lines.append(
            f"| {row.installment_number} "
            f"| {row.due_date.strftime('%d/%m/%Y')} "
            f"| {money(row.opening_balance)} "
            f"| {money(row.interest_amount)} "
            f"| {money(row.amortization_amount)} "
            f"| {money(row.installment_amount)} "
            f"| {money(row.closing_balance)} |"
        )
    lines.append("")

    lines.append("### Resultados\n")
    lines.append("| Variable | Valor |")
    lines.append("| --- | --- |")
    lines.append(f"| Tasa efectiva por periodo | {schedule.periodic_rate_percent} % |")
    lines.append(f"| Cuota constante | {money(schedule.installment_amount)} |")
    lines.append(f"| Interes total | {money(schedule.total_interest)} |")
    lines.append(f"| Total a pagar | {money(schedule.total_payment)} |")
    lines.append(f"| TCEA | {schedule.tcea} % |")
    lines.append(f"| **Saldo final** | **{money(schedule.final_balance)}** |\n")

    if schedule.rows[-1].installment_amount != schedule.installment_amount:
        difference = schedule.rows[-1].installment_amount - schedule.installment_amount
        lines.append(
            f"> Nota: la ultima cuota es {money(schedule.rows[-1].installment_amount)} y no "
            f"{money(schedule.installment_amount)} (diferencia de {money(difference)}). "
            "Es el ajuste de redondeo que absorbe la ultima cuota para que el saldo "
            "cierre exactamente en S/ 0.00.\n"
        )

    return "\n".join(lines)


def write_test_cases() -> None:
    parts = [
        "# Anexo C — Cronogramas de prueba\n",
        GENERATED_NOTE,
        "\nCasos de prueba del motor financiero. Los mismos numeros estan verificados "
        "por `pytest` en `apps/api/tests/test_finance.py`.\n",
        "\nConvenciones: metodo frances, base 360 dias, tasas con 7 decimales en "
        "porcentaje e importes con 2 decimales.\n\n",
    ]
    for case in ACADEMIC_CASES:
        parts.append(schedule_section(case, run_case(case)))
        parts.append("\n---\n\n")
    (DOCS_DIR / "test-cases.md").write_text("".join(parts), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════
# Anexo F - evidencias de validacion
# ══════════════════════════════════════════════════════════════════════════


def comparison_rows(case: AcademicCase, schedule: Schedule) -> list[tuple[str, str, str]]:
    """(variable, esperado, obtenido) - el esperado viene del calculo a mano."""
    rows: list[tuple[str, str, str]] = [
        (
            "Tasa efectiva por periodo (%)",
            str(case.expected_periodic_rate_percent),
            str(schedule.periodic_rate_percent),
        ),
        ("Cuota constante", str(case.expected_installment), str(schedule.installment_amount)),
        ("Interes total", str(case.expected_total_interest), str(schedule.total_interest)),
        ("Total a pagar", str(case.expected_total_payment), str(schedule.total_payment)),
        ("Saldo final", str(case.expected_final_balance), str(schedule.final_balance)),
    ]
    for expected, row in zip(case.expected_rows, schedule.rows, strict=True):
        number = expected.installment_number
        rows.append(
            (f"Cuota {number} — interes", str(expected.interest_amount), str(row.interest_amount))
        )
        rows.append(
            (
                f"Cuota {number} — amortizacion",
                str(expected.amortization_amount),
                str(row.amortization_amount),
            )
        )
        rows.append(
            (
                f"Cuota {number} — saldo final",
                str(expected.closing_balance),
                str(row.closing_balance),
            )
        )
    return rows


def validation_table(case: AcademicCase, schedule: Schedule) -> str:
    lines = [f"### {case.title}\n"]
    lines.append("| Variable | Esperado | Sistema | Diferencia | Resultado |")
    lines.append("| --- | ---: | ---: | ---: | :---: |")
    for variable, expected, obtained in comparison_rows(case, schedule):
        # Quantize against the expected value so a zero difference prints as
        # 0.0000000 instead of Decimal's scientific 0E-7.
        difference = (Decimal(obtained) - Decimal(expected)).quantize(Decimal(expected))
        verdict = "OK" if difference == 0 else "REVISAR"
        lines.append(
            f"| {variable} | {expected} | {obtained} | {difference:+f} | {verdict} |"
        )
    lines.append("")
    return "\n".join(lines)


def pytest_summary() -> str:
    """Run the suite so the annex reports a real result, not a claim."""
    result = subprocess.run(
        ["uv", "run", "pytest", "-q", "--no-header"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = [line for line in result.stdout.strip().splitlines() if line.strip()]
    return tail[-1] if tail else "sin salida"


def write_validation() -> None:
    schedules = {case.key: run_case(case) for case in ACADEMIC_CASES}
    summary = pytest_summary()

    parts = [
        "# Anexo F — Evidencias de validacion\n",
        GENERATED_NOTE,
        f"\nGenerado el {date.today().strftime('%d/%m/%Y')}.\n",
        "\n## 1. Como obtener cada evidencia\n",
        """
| # | Evidencia | Como obtenerla |
| --- | --- | --- |
| 1 | Ejecucion de la bateria de tests | `cd apps/api && uv run pytest -v` |
| 2 | Resultado del caso de prueba 1 | `uv run pytest -v -k caso-1` |
| 3 | Resultado del caso de prueba 2 | `uv run pytest -v -k caso-2` |
| 4 | Respuesta JSON de `/credits/simulate` | Ver el comando del punto 4 mas abajo |
| 5 | Captura del frontend con el cronograma | [docs/evidence/04-simulador-cronograma.png](evidence/04-simulador-cronograma.png), o abrir http://localhost:5173 -> Nuevo credito -> Simular |
| 6 | Comparacion esperado vs obtenido | Tabla de la seccion 5 de este documento |
| 7 | Saldo final = 0 | Ultima fila de cada cronograma en [Anexo C](test-cases.md) |
| 8 | Contraste contra Excel | [prestameami-cronogramas.xlsx](evidence/prestameami-cronogramas.xlsx) — ver seccion 5 |
""",
        "\n### Comando para la evidencia 4\n",
        """
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"admin@prestameami.pe","password":"admin123"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/credits/simulate \\
  -H "Authorization: Bearer $TOKEN" \\
  -H 'Content-Type: application/json' \\
  -d '{
    "client_id": 1,
    "amount": "140.00",
    "rate_type": "TEA",
    "annual_rate": "40.00",
    "start_date": "2026-09-12",
    "term_days": 14,
    "installments_count": 2,
    "payment_frequency_days": 7,
    "grace_type": "none",
    "grace_days": 0
  }' | jq
```
""",
        "\n## 2. Resultado de la bateria de tests\n",
        f"\n```\n$ uv run pytest -q\n{summary}\n```\n",
        "\nLos tests cubren la conversion de tasas, el metodo frances, la tasa cero, "
        "los limites de monto y plazo, los periodos de gracia, el interes moratorio, "
        "el bloqueo de clientes morosos y el flujo completo de la demo por HTTP.\n",
        "\n## 3. Capturas de la aplicacion\n",
        """
Capturadas sobre la aplicacion en ejecucion (API en el puerto 8000 y frontend
en el 5173) con la base cargada por `scripts/seed.py`.

### Simulador con el cronograma frances

![Simulador de credito](evidence/04-simulador-cronograma.png)

Credito de S/ 140.00 a TEA 40 %, 14 dias, 2 cuotas cada 7 dias. La tasa
periodica es 0.6563965 %, la cuota S/ 70.69, el interes total S/ 1.38, el total
a pagar S/ 141.38 y el **saldo final S/ 0.00**. Los mismos numeros que devuelve
`POST /api/credits/simulate` y que verifican los tests.

### Dashboard

![Dashboard](evidence/02-dashboard.png)

### Clientes

![Clientes](evidence/03-clientes.png)

### Morosos y clientes bloqueados

![Morosos](evidence/05-morosos.png)

### Interfaz en ingles (i18n)

![Dashboard en ingles](evidence/06-dashboard-en.png)
""",
        "\n## 4. Contraste contra Excel\n",
        """
El archivo [prestameami-cronogramas.xlsx](evidence/prestameami-cronogramas.xlsx)
reconstruye los dos casos **con formulas vivas de Excel**, no con numeros
pegados. Cada hoja trae abajo una tabla que resta lo que calcula Excel menos lo
que devuelve el sistema; la columna Diferencia debe dar 0.00 en todas las filas.

| Concepto | Formula en la hoja |
| --- | --- |
| Tasa periodica | `=REDONDEAR((1+TEA)^(dias/360)-1; 9)` |
| Cuota | `=REDONDEAR(PAGO(i; n; -P); 2)` |
| Interes del periodo | `=REDONDEAR(saldo_anterior * i; 2)` |
| Amortizacion | `=REDONDEAR(cuota - interes; 2)` |
| Saldo | `=REDONDEAR(saldo_anterior - amortizacion; 2)` |
| Ultima cuota | amortiza todo el saldo restante, para cerrar en 0.00 |

La hoja **Simulador libre** permite cambiar capital, TEA, numero de cuotas y
frecuencia, y recalcula el cronograma completo dentro de Excel.

Esta equivalencia no se afirma de palabra: `tests/test_excel.py` regenera el
libro, se lo entrega a LibreOffice para que **recalcule de verdad** todas las
formulas, y compara celda por celda contra el motor. Si alguna vez divergen, la
bateria de tests se pone en rojo.

Para regenerarlo:

```bash
cd apps/api && uv run python scripts/generate_excel.py
```
""",
        "\n## 5. Comparacion esperado vs obtenido\n",
        "\nLa columna **Esperado** son los valores calculados a mano con las "
        "formulas del enunciado (definidos en "
        "`apps/api/scripts/academic_cases.py`). La columna **Sistema** es lo que "
        "devuelve el motor al ejecutarse ahora mismo.\n\n",
    ]
    for case in ACADEMIC_CASES:
        parts.append(validation_table(case, schedules[case.key]))
        parts.append("\n")

    all_ok = all(
        Decimal(obtained) - Decimal(expected) == 0
        for case in ACADEMIC_CASES
        for _, expected, obtained in comparison_rows(case, schedules[case.key])
    )
    parts.append(
        "\n## 6. Conclusion\n\n"
        + (
            "Todas las variables comparadas coinciden exactamente con el calculo "
            "manual: diferencia de 0.00 en cada fila. El saldo final de ambos "
            "cronogramas cierra en S/ 0.00, como exige el metodo frances.\n"
            if all_ok
            else "Hay diferencias entre el calculo manual y el sistema. Revisar las "
            "filas marcadas como REVISAR.\n"
        )
    )
    (DOCS_DIR / "validation.md").write_text("".join(parts), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════
# Anexo E - ERD, read straight off the SQLAlchemy metadata
# ══════════════════════════════════════════════════════════════════════════

#: Table name -> the entity name used in the academic ERD.
ENTITIES = {
    "users": "USER",
    "clients": "CLIENT",
    "credits": "CREDIT",
    "installments": "INSTALLMENT",
    "payments": "PAYMENT",
}

RELATIONSHIPS = [
    ("CLIENT", "||--o{", "CREDIT", "recibe"),
    ("CREDIT", "||--|{", "INSTALLMENT", "se divide en"),
    ("CREDIT", "||--o{", "PAYMENT", "acumula"),
    ("INSTALLMENT", "||--o{", "PAYMENT", "se cobra con"),
]


def column_type(column) -> str:  # noqa: ANN001
    """Short, readable type label for the diagram."""
    kind = column.type
    if isinstance(kind, DecimalText):
        return f"decimal_{kind.decimals}"
    if isinstance(kind, SAEnum):
        return "enum"
    if isinstance(kind, Integer):
        return "int"
    if isinstance(kind, DateTime):
        return "datetime"
    if isinstance(kind, Date):
        return "date"
    if isinstance(kind, String):
        return "string"
    return type(kind).__name__.lower()


def write_erd() -> None:
    """Emit the ER diagram from Base.metadata - the database IS the document."""
    import app.models  # noqa: F401  (registers the tables)

    lines = [
        "# Anexo E — Diagrama entidad-relacion (ERD)\n",
        GENERATED_NOTE,
        "\nEl diagrama se lee directamente de `Base.metadata`, es decir de las "
        "tablas que el sistema crea de verdad. Si una columna no aparece aca es "
        "porque no existe en la base, y al reves.\n",
        "\n```mermaid",
        "erDiagram",
    ]

    for table_name, entity in ENTITIES.items():
        table = Base.metadata.tables[table_name]
        lines.append(f"    {entity} {{")
        for column in table.columns:
            marks = []
            if column.primary_key:
                marks.append("PK")
            if column.foreign_keys:
                marks.append("FK")
            suffix = f" {','.join(marks)}" if marks else ""
            lines.append(f"        {column_type(column)} {column.name}{suffix}")
        lines.append("    }")

    for left, cardinality, right, label in RELATIONSHIPS:
        lines.append(f"    {left} {cardinality} {right} : \"{label}\"")

    lines.append("```\n")

    lines.append("\n## Cardinalidades\n")
    lines.append("| Relacion | Cardinalidad | Lectura |")
    lines.append("| --- | --- | --- |")
    lines.append(
        "| CLIENT — CREDIT | 1:N | Un cliente puede recibir varios creditos; "
        "cada credito pertenece a un solo cliente. |"
    )
    lines.append(
        "| CREDIT — INSTALLMENT | 1:N | Un credito se divide en una o mas cuotas "
        "(minimo una, por eso la barra doble). |"
    )
    lines.append(
        "| CREDIT — PAYMENT | 1:N | Un credito acumula cero o mas pagos. |"
    )
    lines.append(
        "| INSTALLMENT — PAYMENT | 1:N | Una cuota puede cobrarse en varios pagos "
        "parciales. |"
    )
    lines.append(
        "| USER | — | El administrador de la aplicacion. No se relaciona con los "
        "clientes de la bodega: son personas distintas. |\n"
    )

    lines.append("\n## Dominios de los campos enum\n")
    lines.append("| Entidad | Campo | Valores |")
    lines.append("| --- | --- | --- |")
    lines.append("| CLIENT | credit_status | `enabled`, `blocked` |")
    lines.append("| CREDIT | rate_type | `TNA`, `TEA` |")
    lines.append("| CREDIT | grace_type | `none`, `partial`, `total` |")
    lines.append("| CREDIT | status | `active`, `paid`, `overdue` |")
    lines.append("| INSTALLMENT | status | `pending`, `paid`, `overdue` |")
    lines.append("| PAYMENT | payment_method | `cash`, `yape`, `plin`, `transfer` |\n")

    lines.append("\n## Notas de diseno\n")
    lines.append(
        "- **`decimal_2` y `decimal_9`.** SQLite no tiene tipo decimal nativo. Los "
        "importes se guardan como TEXT y vuelven como `Decimal` de Python, asi el "
        "saldo final es exactamente `0.00` y no un float con cola. `decimal_2` son "
        "importes en soles; `decimal_9` es la tasa periodica como fraccion, que "
        "equivale a 7 decimales cuando se muestra en porcentaje.\n"
    )
    lines.append(
        "- **No hay columna `paid_amount` en INSTALLMENT.** Cuanto se pago de una "
        "cuota se deduce sumando sus PAYMENT. Guardarlo ademas seria un dato "
        "duplicado que se puede desincronizar.\n"
    )
    lines.append(
        "- **No hay columna de tasa moratoria.** Es un parametro del sistema, igual "
        "para todos los creditos, y vive en la configuracion del backend "
        "(`app/core/config.py`). Se expone en `GET /api/config`.\n"
    )
    lines.append(
        "- **No hay columna `code`.** El codigo visible del credito (`CR-0021`) se "
        "deriva del `id`.\n"
    )
    lines.append(
        "- **No hay tabla de configuracion.** La pantalla de Configuracion muestra "
        "los parametros en solo lectura, precisamente para no crear una tabla que "
        "el ERD academico no contempla.\n"
    )

    (DOCS_DIR / "erd.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    write_test_cases()
    write_validation()
    write_erd()
    for name in ("test-cases.md", "validation.md", "erd.md"):
        print(f"Generado: {DOCS_DIR / name}")


if __name__ == "__main__":
    main()
