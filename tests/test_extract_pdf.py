"""Sanity test for the PDF extractor.

No real AVL X-Meter certificate PDF was available while building this app.
This test generates a synthetic certificate PDF that follows the field/table
layout described in SPEC.md (one label + value(s) per line) and checks that
extract_pdf.extract() recovers the same numbers that went in. It exercises
the label-matching and number-parsing logic; it does NOT prove the real
certificate's PDF layout matches (fonts, exact wording and table structure
could differ) - see README.md for the required manual review step.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from avl_report.extract_pdf import extract
from avl_report.models import CalibrationData

EXAMPLE = json.loads(Path(__file__).parent.parent.joinpath("examples/example_data.json").read_text())


def _make_synthetic_certificate(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800

    def line(text):
        nonlocal y
        c.drawString(50, y, text)
        y -= 16

    # Page 1: header
    line("AVL X-Meter Calibration Certificate")
    line(f"Calibration Date {EXAMPLE['calibration_date']}")
    line(f"Report ID {EXAMPLE['report_id']}")
    line(f"Device {EXAMPLE['device']}")
    line(f"Serial No {EXAMPLE['serial_no']}")
    line(f"DVM Manufacturer {EXAMPLE['dvm_manufacturer']}")
    line(f"DVM Type {EXAMPLE['dvm_type']}")
    line(f"DVM Gage No {EXAMPLE['dvm_gage_no']}")
    line(f"DVM Calibration Date {EXAMPLE['dvm_calibration_date']}")
    line(f"Ambient Temperature {EXAMPLE['ambient_temperature']}")
    line(f"Relative Humidity {EXAMPLE['relative_humidity']}")
    c.showPage()

    # Page 2: +/-10V, channels 1-8
    y = 800
    r10 = EXAMPLE["r10"]
    volt_str = " ".join(f"{v:.1f}".replace(".", ",") for v in r10["voltages"])
    line(f"Calibration Voltage (2) [V] {volt_str}")
    for ch in range(1, 9):
        err_str = " ".join(f"{e:.5f}".replace(".", ",") for e in r10["errors"][str(ch)])
        line(f"Error Channel{ch} [V] {err_str}")
    c.showPage()

    # Page 3: +/-20V (ch9), +/-75V (ch10)
    y = 800
    r20 = EXAMPLE["r20"]
    volt_str = " ".join(f"{v:.1f}".replace(".", ",") for v in r20["voltages"])
    line(f"Calibration Voltage (2) [V] {volt_str}")
    err_str = " ".join(f"{e:.5f}".replace(".", ",") for e in r20["errors"]["9"])
    line(f"Error Channel9 [V] {err_str}")
    y -= 10
    r75 = EXAMPLE["r75"]
    volt_str = " ".join(f"{v:.1f}".replace(".", ",") for v in r75["voltages"])
    line(f"Calibration Voltage (2) [V] {volt_str}")
    err_str = " ".join(f"{e:.5f}".replace(".", ",") for e in r75["errors"]["10"])
    line(f"Error Channel10 [V] {err_str}")
    c.showPage()
    c.save()


def test_extract_synthetic_certificate(tmp_path):
    pdf_path = tmp_path / "synthetic_cert.pdf"
    _make_synthetic_certificate(pdf_path)

    draft = extract(pdf_path)
    assert draft.data is not None, f"extraction failed, warnings: {draft.warnings}"

    expected = CalibrationData.from_dict(EXAMPLE)
    d = draft.data
    assert d.serial_no == expected.serial_no
    assert d.report_id == expected.report_id
    assert d.r10.voltages == expected.r10.voltages
    for ch in range(1, 9):
        assert d.r10.errors[ch] == expected.r10.errors[ch]
    assert d.r20.voltages == expected.r20.voltages
    assert d.r20.errors[9] == expected.r20.errors[9]
    assert d.r75.voltages == expected.r75.voltages
    assert d.r75.errors[10] == expected.r75.errors[10]


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_extract_synthetic_certificate(Path(tmp))
    print("OK")
