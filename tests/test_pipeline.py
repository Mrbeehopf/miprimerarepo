"""End-to-end smoke test: example_data.json -> xlsx -> LibreOffice recalc ->
results -> pdf. Requires libreoffice-calc to be installed (headless
recalculation). Run directly with `python3 tests/test_pipeline.py` or via
pytest.
"""
from __future__ import annotations

from pathlib import Path

from avl_report.build_pdf import render_pdf
from avl_report.build_xlsx import build_workbook
from avl_report.extract_results import extract_channel_results
from avl_report.models import CalibrationData
from avl_report.recalc import recalculate
from avl_report.validate import plausibility_check

EXAMPLE = Path(__file__).parent.parent / "examples" / "example_data.json"


def test_full_pipeline(tmp_path):
    data = CalibrationData.load(EXAMPLE)
    assert plausibility_check(data) == []

    xlsx_path = tmp_path / "report.xlsx"
    build_workbook(data, xlsx_path)
    assert xlsx_path.exists()

    recalculate(xlsx_path)
    results = extract_channel_results(xlsx_path, data)
    assert len(results) == 10
    assert all(r["state"] == "PASSED" for r in results), [
        (r["sheet"], r["state"]) for r in results
    ]

    pdf_path = tmp_path / "report.pdf"
    render_pdf(results, data, pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_full_pipeline(Path(tmp))
    print("OK")
