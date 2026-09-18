"""Render the 10-page AVL-style Linearity Verification PDF report.

Ported from the validated reference script `reference_build_pdf.py`; layout,
colors and German number formatting are kept unchanged. Parametrized on the
channel-results list (from extract_results.py), the certificate info, an
optional logo image, and the output path (instead of hardcoded globals).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from .models import CalibrationData

YELLOW = colors.Color(1, 1, 0)
BLUEBAR = colors.Color(0x4F / 255, 0x81 / 255, 0xBD / 255)
GREY = colors.Color(0xD9 / 255, 0xD9 / 255, 0xD9 / 255)
GREEN = colors.Color(0x92 / 255, 0xD0 / 255, 0x50 / 255)
RED = colors.Color(1, 0, 0)
LOGO_AR = 354 / 826  # height/width of the reference AVL logo


def _de(x: float, dec: int) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def render_pdf(
    chan: List[dict],
    data: CalibrationData,
    out_path: Path,
    logo_path: Optional[Path] = None,
) -> Path:
    info = data.info
    serial, report = info["Serial No"], info["Report ID"]
    caldate, dvmcal = info["Calibration Date"], info["DVM Calibration Date"]
    dvm_serial = "PM" + str(info["DVM Gage No"])

    logo = ImageReader(str(logo_path)) if logo_path and Path(logo_path).exists() else None

    W, H = A4
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    LM = 18 * mm
    RM = W - 14 * mm

    def draw_page(ch):
        y = H - 20 * mm
        c.setFont("Helvetica", 20)
        c.setFillColor(colors.black)
        c.drawString(LM, y, "Linearity Verification - Voltage")
        if logo is not None:
            lw = 34 * mm
            lh = lw * LOGO_AR
            c.drawImage(logo, RM - lw, y - 2, lw, lh, mask="auto")
        y -= 6 * mm

        def section_bar(label, yy):
            c.setFillColor(BLUEBAR)
            c.rect(LM, yy - 1.5 * mm, RM - LM, 5 * mm, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(LM + 1 * mm, yy, label)
            return yy - 6.5 * mm

        def field(label, val, yy, yellow=True, wide=False):
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.black)
            c.drawString(LM + 1 * mm, yy, label)
            vx = LM + 38 * mm
            vw = (RM - vx) if wide else 78 * mm
            if yellow:
                c.setFillColor(YELLOW)
                c.rect(vx, yy - 1.2 * mm, vw, 4.6 * mm, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(vx + 0.8 * mm, yy, str(val))
            return yy - 4.9 * mm

        y = section_bar("Test Data", y)
        y = field("Measurement Type:", "Voltage", y)
        y = field("Instrument:", "AVL X-Meter", y)
        y = field("Serial Number:", str(serial), y)
        y = field("Instrument Range:", ch["range"], y)
        y = field("Order / Device:", "SEMA / X-Meter", y)
        y = field("Calibration Date:", str(caldate), y)
        y = field("Report ID:", str(report), y, yellow=False)
        y = field("Legislation:", "§ 1065.307 Linearity verification. - [79 FR 23766, Apr. 28, 2014]", y, wide=True)
        y -= 3 * mm
        y = section_bar("Reference Device Data", y)
        y = field("Description:", "Fluke 8588A DVM digital voltage meter", y)
        y = field("Manufacturer:", info["DVM Manufacturer"], y)
        y = field("Serial Number:", dvm_serial, y)
        y = field("Calibration Date:", str(dvmcal), y)
        y = field("Instrument Range:", "100 mV to 1000 V", y)
        y -= 3 * mm
        y = section_bar("Test Results", y)
        colw = [(RM - LM) * 0.50, (RM - LM) * 0.25, (RM - LM) * 0.25]
        tdata = [
            ["Description", "Calculated", "Limits"],
            ["a1 Slope", _de(ch["a1"], 7), ch["a1lim"].replace(".", ",")],
            ["|Xmin(a1-1)+a0| Interception", _de(ch["ic"], 7), ch["iclim"].replace(".", ",")],
            ["SEE Standard Estimation of Error", _de(ch["see"], 7), ch["seelim"].replace(".", ",")],
            ["r² Coefficient", _de(ch["r2"], 7), ch["r2lim"].replace(".", ",")],
            ["Test State", ch["state"], ""],
        ]
        t = Table(tdata, colWidths=colw, rowHeights=[5.2 * mm] * 6)
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Oblique", 8.5), ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
            ("ALIGN", (1, 0), (2, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey), ("LINEBELOW", (0, -2), (-1, -2), 0.5, colors.grey),
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.grey), ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (1, 5), (1, 5), GREEN if ch["state"] == "PASSED" else RED),
            ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.grey), ("LINEAFTER", (1, 0), (1, -1), 0.5, colors.grey),
            ("LINEBEFORE", (0, 0), (0, -1), 0.5, colors.grey), ("LINEAFTER", (2, 0), (2, -1), 0.5, colors.grey),
        ]))
        tw, th = t.wrap(0, 0)
        t.drawOn(c, LM, y - th + 5.2 * mm)
        y = y - th
        y -= 6 * mm
        hdr = ["Index", "Reference [V]", "Sample [V]", "Dev. [V]", "Dev. [%]"]
        rows = [hdr]
        for i, rw in enumerate(ch["rows"], 1):
            ref, samp, dv, dp = rw
            rows.append([str(i), _de(ref, 6), _de(samp, 6), _de(dv, 5), _de(dp, 5)])
        total_rows = 16
        ndata = len(ch["rows"])
        for _ in range(total_rows - ndata):
            rows.append(["", "", "", "", ""])
        cw = [(RM - LM) * 0.14, (RM - LM) * 0.235, (RM - LM) * 0.235, (RM - LM) * 0.195, (RM - LM) * 0.195]
        dt = Table(rows, colWidths=cw, rowHeights=[5.0 * mm] * (total_rows + 1))
        dt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5), ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, 0), GREY), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (1, 1), (2, total_rows), YELLOW),
        ]))
        tw, th = dt.wrap(0, 0)
        dt.drawOn(c, LM, y - th + 5.0 * mm)
        y = y - th
        y -= 6 * mm
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        c.drawString(LM, y, "Notes: Linearity Check Version 3.0")
        y -= 5 * mm
        box = ["GPN: 1*", "Document No: D01*", "SAP Material No: TNA99M*", "Change No: TSI-0*", "Revision: 00"]
        bh = len(box) * 4.3 * mm + 2 * mm
        c.setStrokeColor(colors.grey)
        c.rect(LM, y - bh + 3.5 * mm, RM - LM, bh, fill=0, stroke=1)
        yy = y
        for ln in box:
            c.drawString(LM + 1.5 * mm, yy, ln)
            yy -= 4.3 * mm
        c.showPage()

    for ch in chan:
        draw_page(ch)
    c.save()
    return out_path
