"""Best-effort extraction of calibration data from an AVL X-Meter
Kalibrierzertifikat PDF (see SPEC.md §1 for the exact 3-page layout).

No original certificate PDF was available while building this app, so this
extractor is implemented directly from the SPEC's field/table description
and validated against a synthetically generated certificate of the same
layout (see tests/). Because the extracted values are safety-critical
(SPEC.md §6), this module never silently trusts its own output: `extract()`
returns a `CalibrationDraft` that also carries `warnings` for anything it
could not find or parse, and the CLI always shows the draft to the user for
review/confirmation before it is used to build a report.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

from .models import CalibrationData, RangeData

_NUM_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _to_float(tok: str) -> float:
    return float(tok.replace(",", "."))


@dataclass
class CalibrationDraft:
    data: Optional[CalibrationData]
    warnings: List[str] = field(default_factory=list)


def _find_value_after_label(text: str, label: str) -> Optional[str]:
    """Find `label` in `text` and return the remainder of that line, or the
    next non-empty line if the label is alone on its line."""
    lines = [ln.strip() for ln in text.splitlines()]
    for i, ln in enumerate(lines):
        if label.lower() in ln.lower():
            rest = ln[ln.lower().find(label.lower()) + len(label):].strip(" :\t")
            if rest:
                return rest
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j]:
                    return lines[j]
    return None


def _label_occurrences(page: "fitz.Page", label: str, y_tol: float = 3.0) -> List[tuple]:
    """Find every occurrence of `label` on the page and return a list of
    (y_center, numbers) for the numeric tokens on that same text line
    (matched by y-coordinate band), in left-to-right order."""
    words = page.get_text("words")  # (x0,y0,x1,y1, text, block,line,word_no)
    label_tokens = label.lower().split()
    occurrences = []
    for i in range(len(words)):
        if words[i][4].lower().rstrip(":") != label_tokens[0]:
            continue
        matched = True
        for k, lt in enumerate(label_tokens[1:], start=1):
            if i + k >= len(words) or words[i + k][4].lower().rstrip(":") != lt:
                matched = False
                break
        if not matched:
            continue
        y_center = (words[i][1] + words[i][3]) / 2
        label_end_x = words[i + len(label_tokens) - 1][2]
        nums = []
        for w in words:
            wy_center = (w[1] + w[3]) / 2
            if abs(wy_center - y_center) <= y_tol and w[0] >= label_end_x - 1:
                if _NUM_RE.fullmatch(w[4].strip()):
                    nums.append((w[0], _to_float(w[4])))
        nums.sort(key=lambda t: t[0])
        if nums:
            occurrences.append((y_center, [n for _, n in nums]))
    return occurrences


def _nearest(occurrences: List[tuple], target_y: float) -> Optional[List[float]]:
    if not occurrences:
        return None
    return min(occurrences, key=lambda oy: abs(oy[0] - target_y))[1]


def _extract_range(page: "fitz.Page", channels: List[int], warnings: List[str], range_name: str) -> Optional[Dict]:
    """Extract the 'Calibration Voltage' row and the 'Error ChannelX' rows
    for one range section. `page` may contain more than one such section
    (e.g. page 3 has both +/-20V and +/-75V); occurrences are disambiguated
    by picking the Calibration Voltage row closest (in y) to each channel's
    Error Channel row, since within one section they are adjacent lines."""
    voltage_occurrences = _label_occurrences(page, "Calibration Voltage")
    if not voltage_occurrences:
        warnings.append(f"{range_name}: 'Calibration Voltage' row not found - manual entry required.")
        return None
    errors = {}
    voltages = None
    for ch in channels:
        err_occurrences = _label_occurrences(page, f"Error Channel{ch}")
        if not err_occurrences:
            warnings.append(f"{range_name}: 'Error Channel{ch}' row not found - manual entry required.")
            continue
        err_y, errs = err_occurrences[0]
        errors[ch] = errs
        if voltages is None:
            voltages = _nearest(voltage_occurrences, err_y)
    if voltages is None:
        warnings.append(f"{range_name}: could not associate a 'Calibration Voltage' row - manual entry required.")
        return None
    for ch, errs in errors.items():
        if len(errs) != len(voltages):
            warnings.append(
                f"{range_name} Channel{ch}: found {len(errs)} error values but "
                f"{len(voltages)} voltage points - please verify."
            )
    return {"voltages": voltages, "errors": errors}


def extract(pdf_path: Path) -> CalibrationDraft:
    warnings: List[str] = []
    doc = fitz.open(str(pdf_path))
    if doc.page_count < 3:
        warnings.append(f"Expected 3 pages, found {doc.page_count}.")

    page1_text = doc[0].get_text()
    header_fields = {
        "calibration_date": "Calibration Date",
        "report_id": "Report ID",
        "device": "Device",
        "serial_no": "Serial No",
        "dvm_manufacturer": "DVM Manufacturer",
        "dvm_type": "DVM Type",
        "dvm_gage_no": "DVM Gage No",
        "dvm_calibration_date": "DVM Calibration Date",
        "ambient_temperature": "Ambient Temperature",
        "relative_humidity": "Relative Humidity",
    }
    header: Dict[str, str] = {}
    for key, label in header_fields.items():
        val = _find_value_after_label(page1_text, label)
        if val is None:
            warnings.append(f"Header field '{label}' not found - manual entry required.")
            val = ""
        header[key] = val

    page2 = doc[1] if doc.page_count > 1 else None
    page3 = doc[2] if doc.page_count > 2 else None

    r10_raw = _extract_range(page2, list(range(1, 9)), warnings, "±10V") if page2 else None
    r20_raw = _extract_range(page3, [9], warnings, "±20V") if page3 else None
    r75_raw = _extract_range(page3, [10], warnings, "±75V") if page3 else None

    if r10_raw is None or r20_raw is None or r75_raw is None or not header.get("serial_no"):
        doc.close()
        return CalibrationDraft(data=None, warnings=warnings)

    data = CalibrationData(
        calibration_date=header["calibration_date"],
        report_id=header["report_id"],
        device=header["device"] or "AVL X-Meter",
        serial_no=header["serial_no"],
        dvm_manufacturer=header["dvm_manufacturer"] or "Fluke",
        dvm_type=header["dvm_type"] or "8588A",
        dvm_gage_no=header["dvm_gage_no"],
        dvm_calibration_date=header["dvm_calibration_date"],
        ambient_temperature=header["ambient_temperature"],
        relative_humidity=header["relative_humidity"],
        r10=RangeData(
            label="±10V", accuracy_spec="0,010 % Reading + 0,015 % Range",
            voltages=r10_raw["voltages"], errors=r10_raw["errors"],
        ),
        r20=RangeData(
            label="±20V", accuracy_spec="0,500 % Reading + 0,200 % Range",
            voltages=r20_raw["voltages"], errors=r20_raw["errors"],
        ),
        r75=RangeData(
            label="±75V", accuracy_spec="0,500 % Reading + 0,200 % Range",
            voltages=r75_raw["voltages"], errors=r75_raw["errors"],
        ),
    )
    doc.close()
    return CalibrationDraft(data=data, warnings=warnings)


def extract_logo(pdf_path: Path, out_path: Path) -> Optional[Path]:
    """Extract the largest embedded image on page 1 (assumed to be the AVL
    logo) and save it to `out_path`. Returns None if no image is found."""
    doc = fitz.open(str(pdf_path))
    if doc.page_count == 0:
        return None
    page = doc[0]
    images = page.get_images(full=True)
    if not images:
        doc.close()
        return None
    best = None
    best_area = -1
    for img in images:
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        area = pix.width * pix.height
        if area > best_area:
            best_area = area
            best = pix
    if best is None:
        doc.close()
        return None
    if best.colorspace and best.colorspace.n > 3:
        best = fitz.Pixmap(fitz.csRGB, best)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    best.save(str(out_path))
    doc.close()
    return out_path
