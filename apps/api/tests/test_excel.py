"""Cross-check the Excel workbook against the engine.

The workbook is not a dump of our numbers: every cell is a live formula. This
test rebuilds it, hands it to LibreOffice to actually recalculate, and compares
the values LibreOffice produced with the ones the engine produced. If the two
ever drift apart, this goes red.

Skipped when LibreOffice is not installed, so the suite stays green anywhere.
"""

import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.services.finance import build_schedule
from scripts.academic_cases import ACADEMIC_CASES, AcademicCase
from scripts.generate_excel import OUTPUT
from scripts.generate_excel import main as build_workbook

SOFFICE = shutil.which("soffice") or shutil.which("libreoffice")

pytestmark = pytest.mark.skipif(
    SOFFICE is None, reason="LibreOffice no esta instalado: no se puede recalcular el Excel"
)


@pytest.fixture(scope="module")
def recalculated(tmp_path_factory: pytest.TempPathFactory):
    """Rebuild the workbook and let LibreOffice compute every formula."""
    build_workbook()
    out_dir: Path = tmp_path_factory.mktemp("xlsx")
    subprocess.run(
        [
            str(SOFFICE),
            "--headless",
            "--calc",
            "--convert-to",
            "xlsx:Calc MS Excel 2007 XML",
            "--outdir",
            str(out_dir),
            str(OUTPUT),
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    return load_workbook(out_dir / OUTPUT.name, data_only=True)


def _engine(case: AcademicCase):
    return build_schedule(
        amount=case.amount,
        rate_type=case.rate_type,
        annual_rate=case.annual_rate,
        start_date=case.start_date,
        term_days=case.term_days,
        installments_count=case.installments_count,
        payment_frequency_days=case.payment_frequency_days,
    )


def _cell(sheet, reference: str) -> Decimal:
    value = sheet[reference].value
    assert value is not None, f"la celda {reference} quedo vacia"
    return Decimal(str(value))


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_el_excel_reproduce_los_totales_del_sistema(recalculated, case: AcademicCase) -> None:
    schedule = _engine(case)
    sheet = recalculated[case.key.replace("caso-", "Caso ")]

    assert _cell(sheet, "B12") == schedule.periodic_rate
    assert _cell(sheet, "B13") == schedule.installment_amount
    assert _cell(sheet, "B14") == schedule.total_interest
    assert _cell(sheet, "B15") == schedule.total_payment


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_el_excel_reproduce_el_cronograma_fila_por_fila(
    recalculated, case: AcademicCase
) -> None:
    schedule = _engine(case)
    sheet = recalculated[case.key.replace("caso-", "Caso ")]

    for index, row in enumerate(schedule.rows):
        excel_row = 18 + index
        assert _cell(sheet, f"C{excel_row}") == row.opening_balance
        assert _cell(sheet, f"D{excel_row}") == row.interest_amount
        assert _cell(sheet, f"E{excel_row}") == row.amortization_amount
        assert _cell(sheet, f"F{excel_row}") == row.installment_amount
        assert _cell(sheet, f"G{excel_row}") == row.closing_balance


@pytest.mark.parametrize("case", ACADEMIC_CASES, ids=lambda c: c.key)
def test_la_tabla_de_comparacion_del_excel_da_cero(recalculated, case: AcademicCase) -> None:
    """La propia hoja se autoevalua: la columna Diferencia debe ser 0 y decir OK."""
    schedule = _engine(case)
    sheet = recalculated[case.key.replace("caso-", "Caso ")]

    first = 18 + len(schedule.rows) + 4
    for offset in range(5):
        row = first + offset
        difference = Decimal(str(sheet[f"D{row}"].value))
        assert difference == 0, f"{sheet[f'A{row}'].value}: diferencia {difference}"
        assert sheet[f"E{row}"].value == "OK"


def test_el_saldo_final_en_excel_es_exactamente_cero(recalculated) -> None:
    for case in ACADEMIC_CASES:
        schedule = _engine(case)
        sheet = recalculated[case.key.replace("caso-", "Caso ")]
        last_row = 18 + len(schedule.rows) - 1
        assert _cell(sheet, f"G{last_row}") == Decimal("0")


def test_el_simulador_libre_calcula_el_caso_de_la_demo(recalculated) -> None:
    """S/ 140.00, TEA 40 %, 2 cuotas cada 7 dias: el credito que se muestra en vivo."""
    sheet = recalculated["Simulador libre"]
    assert _cell(sheet, "B12") == Decimal("0.006563965")
    assert _cell(sheet, "B13") == Decimal("70.69")
    assert _cell(sheet, "B15") == Decimal("141.38")
    assert _cell(sheet, "G19") == Decimal("0")
    # Con n = 2, las filas 3 a 14 se ocultan solas.
    assert sheet["C20"].value in (None, "")
