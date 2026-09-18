"""Force LibreOffice headless to fully recalculate all formulas in an xlsx
(TRANSPOSE array formulas, VLOOKUP, SLOPE/INTERCEPT/STEYX/CORREL, ...) and
resave it, so the cached values become readable via openpyxl(data_only=True).

By default LibreOffice does NOT recalculate on load/save unless told to; we
achieve this via a throwaway user profile with
`Formula/Load/OOXMLRecalcMode` set to "always", plus an explicit en-US
locale so number-to-text formula results (used for the on-sheet limit
strings) use a period as decimal separator, matching what build_pdf.py
expects before converting to German comma notation.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

# Common install locations LibreOffice does NOT automatically add to PATH,
# especially on Windows (the installer never adds soffice.exe to PATH) and
# on macOS (the binary lives inside the .app bundle).
_FALLBACK_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/opt/libreoffice/program/soffice",
]


def _find_soffice() -> str:
    for name in ("soffice", "soffice.exe"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in _FALLBACK_PATHS:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "LibreOffice (soffice) wurde nicht gefunden - weder im PATH noch an den "
        f"ueblichen Installationsorten ({', '.join(_FALLBACK_PATHS)}).\n"
        "Bitte LibreOffice installieren: https://www.libreoffice.org/download/download/\n"
        f"(erkanntes Betriebssystem: {platform.system()})"
    )

_XCU_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load">
  <prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>2</value></prop>
  <prop oor:name="ODFRecalcMode" oor:op="fuse"><value>2</value></prop>
 </item>
 <item oor:path="/org.openoffice.Office.Linguistic/General">
  <prop oor:name="DefaultLocale" oor:op="fuse"><value>en-US</value></prop>
  <prop oor:name="DefaultLocale_CTL" oor:op="fuse"><value>en-US</value></prop>
  <prop oor:name="DefaultLocale_CJK" oor:op="fuse"><value>en-US</value></prop>
 </item>
 <item oor:path="/org.openoffice.Office.Common/Save/Document">
  <prop oor:name="WarnAlienFormat" oor:op="fuse"><value>false</value></prop>
 </item>
</oor:items>
"""


def _make_profile(profile_dir: Path) -> None:
    registry_dir = profile_dir / "user"
    registry_dir.mkdir(parents=True, exist_ok=True)
    (registry_dir / "registrymodifications.xcu").write_text(_XCU_TEMPLATE, encoding="utf-8")


def recalculate(xlsx_path: Path, timeout: int = 180) -> Path:
    """Recalculate all formulas in `xlsx_path` in place using headless LibreOffice."""
    xlsx_path = Path(xlsx_path).resolve()
    if not xlsx_path.exists():
        raise FileNotFoundError(xlsx_path)

    with tempfile.TemporaryDirectory(prefix="avl_lo_") as tmp:
        tmp_path = Path(tmp)
        profile_dir = tmp_path / "profile"
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        _make_profile(profile_dir)
        soffice = _find_soffice()

        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to", "xlsx:Calc MS Excel 2007 XML",
            "--outdir", str(out_dir),
            str(xlsx_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        result_file = out_dir / xlsx_path.name
        if proc.returncode != 0 or not result_file.exists():
            hint = ""
            if "could not be loaded" in (proc.stdout + proc.stderr):
                hint = (
                    "\nHinweis: dieser Fehler tritt typischerweise auf, wenn nur "
                    "libreoffice-core installiert ist, aber nicht libreoffice-calc. "
                    "Installieren mit: apt-get install -y libreoffice-calc"
                )
            raise RuntimeError(
                "LibreOffice recalculation failed "
                f"(returncode={proc.returncode}).\nstdout={proc.stdout}\nstderr={proc.stderr}{hint}"
            )
        shutil.copyfile(result_file, xlsx_path)
    return xlsx_path
