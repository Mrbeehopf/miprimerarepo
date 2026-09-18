"""Validation per SPEC.md §6.

Two independent checks:
- `plausibility_check`: sanity-checks the extracted/entered calibration
  data itself (point counts, value ranges, sign patterns) before it is
  used to build anything. Warnings only - a real certificate can
  legitimately have unusual-looking values, so this never blocks the run,
  it just surfaces things worth a second look during the mandatory review
  step.
- `compare_to_reference`: if a previously computed results JSON is
  available (e.g. from a prior known-good run), compares a1/interception/
  SEE/r2 per channel with a tight bit-level tolerance (< 2e-6), as required
  by SPEC.md §6.

`DISCLAIMER` is the legal notice SPEC.md §6 requires accompany every
generated report.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import CalibrationData

BIT_TOLERANCE = 2e-6

DISCLAIMER = (
    "Werteuebertragung durch PM (Project Manager / verantwortliche Person), "
    "keine Haftung fuer Richtigkeit der uebertragenen Zertifikatswerte. "
    "Berechnungslogik und Formeln sind validiert. Vor Kundenfreigabe pruefen."
)

_RANGE_MAX = {"r10": 10.0, "r20": 20.0, "r75": 75.0}
_EXPECTED_NPTS = {"r10": 8, "r20": 7, "r75": 7}


def plausibility_check(data: CalibrationData) -> List[str]:
    warnings: List[str] = []
    for key in ("r10", "r20", "r75"):
        rng = getattr(data, key)
        npts = len(rng.voltages)
        expected = _EXPECTED_NPTS[key]
        if npts != expected:
            warnings.append(f"{key}: {npts} Spannungspunkte gefunden, erwartet {expected}.")
        if npts < 3:
            warnings.append(f"{key}: weniger als 3 Punkte ({npts}) - Regression nicht aussagekraeftig.")
        vmax = _RANGE_MAX[key]
        for v in rng.voltages:
            if abs(v) > vmax + 1e-9:
                warnings.append(f"{key}: Spannungswert {v} V liegt ausserhalb des Bereichs ±{vmax} V.")
        if len(set(rng.voltages)) != len(rng.voltages):
            warnings.append(f"{key}: doppelte Spannungswerte in {rng.voltages}.")
        if not rng.errors:
            warnings.append(f"{key}: keine Error-Channel-Werte gefunden.")
        for ch, errs in rng.errors.items():
            if len(errs) != npts:
                warnings.append(
                    f"{key} Kanal {ch}: {len(errs)} Fehlerwerte, aber {npts} Spannungspunkte."
                )
            for e in errs:
                # accuracy spec is roughly 0.5% reading + 0.2% range (worst case
                # for the 20V/75V ranges); flag anything grossly outside that,
                # as it likely indicates a transcription/extraction error.
                bound = 0.02 * vmax + 0.02 * max(abs(x) for x in rng.voltages)
                if abs(e) > bound:
                    warnings.append(
                        f"{key} Kanal {ch}: Fehlerwert {e} V wirkt unplausibel gross "
                        f"(> {bound:.4f} V) - bitte pruefen."
                    )
    if not data.serial_no:
        warnings.append("Serial No fehlt.")
    if not data.report_id:
        warnings.append("Report ID fehlt.")
    if not data.calibration_date:
        warnings.append("Calibration Date fehlt.")
    return warnings


def compare_to_reference(computed: List[dict], reference_path: Path) -> List[str]:
    """Compare computed per-channel a1/ic/see/r2 against a reference results
    JSON (same shape as extract_results.save_results output), tolerance
    < 2e-6 as required by SPEC.md §6."""
    reference = json.loads(Path(reference_path).read_text(encoding="utf-8"))
    ref_by_sheet = {r["sheet"]: r for r in reference}
    problems: List[str] = []
    for ch in computed:
        ref = ref_by_sheet.get(ch["sheet"])
        if ref is None:
            problems.append(f"{ch['sheet']}: kein Referenzwert vorhanden.")
            continue
        for key in ("a1", "ic", "see", "r2"):
            diff = abs(ch[key] - ref[key])
            if diff >= BIT_TOLERANCE:
                problems.append(
                    f"{ch['sheet']} {key}: Abweichung {diff:.2e} >= Toleranz {BIT_TOLERANCE:.0e} "
                    f"(berechnet={ch[key]!r}, referenz={ref[key]!r})."
                )
        if ch["state"] != ref["state"]:
            problems.append(f"{ch['sheet']}: Test State {ch['state']} != Referenz {ref['state']}.")
    return problems
