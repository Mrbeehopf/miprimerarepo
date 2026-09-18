"""CLI entry point: AVL X-Meter Kalibrierzertifikat (PDF) -> Linearity
Verification Report (Excel + PDF).

Usage:
    python -m avl_report.cli --pdf zertifikat.pdf [--outdir out] [--yes]
    python -m avl_report.cli --data data.json [--outdir out] [--yes]

See README.md for the full workflow and SPEC.md for the underlying
calculation logic and required validation steps.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build_pdf import render_pdf
from .build_xlsx import build_workbook
from .extract_pdf import extract, extract_logo
from .extract_results import extract_channel_results, save_results
from .models import CalibrationData
from .recalc import recalculate
from .validate import DISCLAIMER, compare_to_reference, plausibility_check


def _print_draft(data: CalibrationData) -> None:
    print("\n--- Extrahierte / geladene Stammdaten ---")
    for k, v in data.info.items():
        print(f"  {k}: {v}")
    for key in ("r10", "r20", "r75"):
        rng = getattr(data, key)
        print(f"\n  Range {rng.label} ({len(rng.voltages)} Punkte): {rng.voltages}")
        for ch, errs in sorted(rng.errors.items()):
            print(f"    Error Channel{ch}: {errs}")
    print()


def _confirm(data_path: Path, data: CalibrationData) -> CalibrationData:
    while True:
        answer = input(
            f"Werte aus {data_path} uebernehmen? "
            "[j]a weiter / [e]dit Datei & neu laden / [n]ein abbrechen: "
        ).strip().lower()
        if answer in ("j", "y", "ja", "yes"):
            return CalibrationData.load(data_path)
        if answer in ("n", "no", "nein"):
            print("Abgebrochen.")
            sys.exit(1)
        if answer in ("e", "edit"):
            input(f"Bitte {data_path} jetzt bearbeiten und speichern, dann Enter druecken...")
            try:
                data = CalibrationData.load(data_path)
            except Exception as exc:
                print(f"Konnte {data_path} nicht laden: {exc}")
                continue
            _print_draft(data)
            continue
        print("Bitte 'j', 'e' oder 'n' eingeben.")


def run(args: argparse.Namespace) -> int:
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    logo_path = Path(args.logo) if args.logo else None

    if args.pdf:
        pdf_path = Path(args.pdf)
        draft = extract(pdf_path)
        for w in draft.warnings:
            print(f"WARNUNG (Extraktion): {w}")
        if draft.data is None:
            print(
                "\nAutomatische Extraktion unvollstaendig. Bitte die Werte manuell in "
                "eine JSON-Datei eintragen (siehe examples/example_data.json als Vorlage) "
                "und mit --data erneut aufrufen."
            )
            return 1
        data_path = outdir / f"{draft.data.serial_no or 'draft'}_extracted.json"
        draft.data.save(data_path)
        print(f"Entwurf gespeichert: {data_path}")
        _print_draft(draft.data)
        for w in plausibility_check(draft.data):
            print(f"WARNUNG (Plausibilitaet): {w}")
        data = draft.data if args.yes else _confirm(data_path, draft.data)
        if logo_path is None:
            extracted_logo = extract_logo(pdf_path, outdir / "logo.png")
            if extracted_logo:
                logo_path = extracted_logo
                print(f"Logo extrahiert: {logo_path}")
    elif args.data:
        data_path = Path(args.data)
        data = CalibrationData.load(data_path)
        _print_draft(data)
        for w in plausibility_check(data):
            print(f"WARNUNG (Plausibilitaet): {w}")
        if not args.yes:
            answer = input("Mit diesen Werten fortfahren? [j/n]: ").strip().lower()
            if answer not in ("j", "y", "ja", "yes"):
                print("Abgebrochen.")
                return 1
    else:
        print("Fehler: entweder --pdf oder --data angeben.", file=sys.stderr)
        return 2

    base = f"SAO_abs_Linearity_Verification_X-Meter_SN_{data.serial_no}"
    xlsx_path = outdir / f"{base}.xlsx"
    pdf_out_path = outdir / f"{base}.pdf"
    results_path = outdir / f"{base}_chandata.json"

    print(f"\nBaue Excel-Bewertungsdokument: {xlsx_path}")
    build_workbook(data, xlsx_path)

    print("Berechne Formeln neu (LibreOffice headless)...")
    recalculate(xlsx_path)

    print("Extrahiere berechnete Ergebnisse...")
    results = extract_channel_results(xlsx_path, data)
    save_results(results, results_path)

    print(f"Baue PDF-Report: {pdf_out_path}")
    render_pdf(results, data, pdf_out_path, logo_path=logo_path)

    print("\n--- Ergebnis je Kanal ---")
    for ch in results:
        print(f"  {ch['sheet']:>12}: {ch['state']}")

    if args.reference_results:
        problems = compare_to_reference(results, Path(args.reference_results))
        if problems:
            print("\nWARNUNG: Abweichung von Referenzwerten:")
            for p in problems:
                print(f"  {p}")
        else:
            print("\nValidierung gegen Referenzwerte: OK (Toleranz < 2e-6).")

    print(f"\n{DISCLAIMER}")
    print(f"\nFertig:\n  {xlsx_path}\n  {pdf_out_path}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="Pfad zum Kalibrierzertifikat-PDF (AVL X-Meter)")
    src.add_argument("--data", help="Pfad zu einer bereits geprueften Daten-JSON-Datei (ueberspringt PDF-Extraktion)")
    p.add_argument("--outdir", default="out", help="Ausgabeverzeichnis (default: out)")
    p.add_argument("--logo", help="Pfad zu einem Logo-Bild (sonst: aus PDF extrahiert bzw. kein Logo)")
    p.add_argument("--yes", action="store_true", help="Keine interaktive Bestaetigung (nicht empfohlen)")
    p.add_argument("--reference-results", help="Pfad zu einer Referenz-Ergebnis-JSON zum Bit-Abgleich (SPEC.md §6)")
    return p


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
