# AVL X-Meter Report-Generator

App, die ein **AVL X-Meter Kalibrierzertifikat (PDF)** einliest und daraus automatisch
ein **Linearity Verification Bewertungsdokument** erzeugt — als **Excel (.xlsx)** mit
allen Berechnungsformeln und als **PDF** im AVL-Corporate-Stil.

Vorlage (Input) und Ausgabe (Output) sind immer gleich strukturiert. Nur die Zahlenwerte,
Seriennummer, Report-ID und das Kalibrierdatum ändern sich pro Zertifikat.

Die fachliche Spezifikation (Datenfluss, Formeln, Grenzwerte, Layout) steht in [`SPEC.md`](SPEC.md).

## Voraussetzungen

```bash
pip install -r requirements.txt
apt-get install -y libreoffice-calc   # für die Neuberechnung der Excel-Formeln
```

`libreoffice-calc` (nicht nur `libreoffice-core`) wird für Schritt "Excel neu berechnen"
benötigt (TRANSPOSE/VLOOKUP-Formeln liefern sonst keine Werte).

## Verwendung

```bash
# Aus einem Zertifikat-PDF (mit interaktiver Review/Bestätigung, da sicherheitskritisch):
python -m avl_report.cli --pdf zertifikat.pdf --outdir out

# Direkt aus einer bereits geprüften Daten-Datei (überspringt PDF-Extraktion):
python -m avl_report.cli --data examples/example_data.json --outdir out

# Nicht-interaktiv (z.B. für Automatisierung, wenn die Werte schon geprüft sind):
python -m avl_report.cli --data examples/example_data.json --outdir out --yes
```

Ausgabe in `out/`:
- `SAO_abs_Linearity_Verification_X-Meter_SN_<serial>.xlsx`
- `SAO_abs_Linearity_Verification_X-Meter_SN_<serial>.pdf`
- `<serial>_extracted.json` (bei `--pdf`: der Extraktions-Entwurf zum Review)
- `..._chandata.json` (die berechneten Zwischenwerte, zur Nachvollziehbarkeit)

## Ablauf

1. **Extraktion** (`avl_report/extract_pdf.py`): Stammdaten + Calibration-Voltage-Zeilen +
   Error-Channel-Zeilen aus dem PDF lesen (PyMuPDF). Da die Werte sicherheitskritisch sind,
   wird **immer** ein Entwurf gespeichert und zur Bestätigung angezeigt (`--yes` überspringt
   das nur bewusst).
2. **Excel bauen** (`avl_report/build_xlsx.py`): 14-Sheet-Workbook mit allen Formeln
   (SLOPE/INTERCEPT/STEYX/CORREL, TRANSPOSE, VLOOKUP gegen EPA-Grenzwerttabelle).
3. **Neu berechnen** (`avl_report/recalc.py`): LibreOffice headless mit einem eigenen
   Profil (Recalc-Modus "always", Locale en-US) erzwingt vollständige Neuberechnung.
4. **Ergebnisse extrahieren** (`avl_report/extract_results.py`): berechnete a1/Interception/
   SEE/r²/Test-State je Kanal als JSON.
5. **PDF rendern** (`avl_report/build_pdf.py`): 10 Seiten im AVL-Stil, deutsche
   Dezimalformatierung.
6. **Validieren** (`avl_report/validate.py`): Plausibilitätschecks auf die Eingabedaten
   (Punktanzahl, Wertebereich, Vorzeichen) sowie optionaler Bit-Abgleich gegen eine
   Referenz-Ergebnis-JSON (`--reference-results`, Toleranz < 2e-6).

## Wichtige fachliche Punkte (siehe SPEC.md, nicht verändern)

- `Reading = Calibration Voltage + Error` (Kanal-Messwert wird aus Sollspannung + Fehler
  rekonstruiert).
- Interception-Formel nutzt den **vorzeichenbehafteten** Referenzwert am Index des
  kleinsten Absolutwerts (nicht `MIN(ABS)`).
- Grenzwerte skalieren mit `max(|Reference|)` je Kanal, siehe EPA § 1065.307 Tabelle
  ("Voltage"-Zeile).
- Excel-Formeln müssen über LibreOffice neu berechnet werden, sonst liefern
  TRANSPOSE/VLOOKUP keine Werte.

## Status / Einschränkungen

- Es lag beim Bau dieser App **kein echtes Original-Zertifikat-PDF** vor. Die Extraktion
  (`extract_pdf.py`) ist direkt aus der SPEC.md-Beschreibung implementiert und gegen ein
  synthetisch erzeugtes Testzertifikat validiert (`tests/test_extract_pdf.py`), nicht
  gegen das echte Layout. Deshalb ist der Review-/Bestätigungsschritt in der CLI
  **nicht optional** für den produktiven Einsatz — bei unvollständiger Extraktion bitte die
  Werte manuell in einer JSON-Datei (Vorlage: `examples/example_data.json`) nachtragen
  und mit `--data` weiterverarbeiten.
- Excel-Aufbau, PDF-Layout und Berechnungslogik sind 1:1 aus den validierten
  Referenzskripten (`reference_build_xlsx.py`, `reference_build_pdf.py`) übernommen und
  gegen die Beispieldaten (`examples/example_data.json`, transkribiert aus Zertifikat
  SN 61510192) end-to-end getestet — alle 10 Kanäle ergeben `PASSED`
  (`tests/test_pipeline.py`).

## Rechtlicher Hinweis (SPEC.md §6)

Werteübertragung durch PM, keine Haftung für Richtigkeit der übertragenen
Zertifikatswerte. Berechnungslogik und Formeln sind validiert. Vor Kundenfreigabe prüfen.
Dieser Hinweis wird am Ende jedes CLI-Laufs ausgegeben.
