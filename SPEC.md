# Spezifikation: AVL X-Meter Kalibrierzertifikat → Linearity Verification Report

## Ziel
Eine App/Skript-Pipeline, die ein **AVL X-Meter Kalibrierzertifikat (PDF)** einliest und daraus
automatisch ein **Linearity Verification Bewertungsdokument** erzeugt — sowohl als
**Excel (.xlsx)** mit allen Berechnungsformeln als auch als **PDF** im AVL-Corporate-Stil.

Vorlage (Input) und Ausgabe (Output) sind immer gleich strukturiert. Nur die Zahlenwerte,
Seriennummer, Report-ID und Kalibrierdatum ändern sich pro Zertifikat.

---

## 1. INPUT: Struktur des Kalibrierzertifikats (3 Seiten)

### Seite 1 — Stammdaten
- Calibration Date (z.B. `2026/08/06`)
- Report ID (z.B. `AVL X-Meter_61510192_202608061326`)
- Device: `AVL X-Meter`
- Serial No (z.B. `61510192`)
- DVM Manufacturer: `Fluke`, DVM Type: `8588A`, DVM Gage No: `1393`
- DVM Calibration Date (z.B. `19.02.2026`)
- Ambient Temperature (z.B. `23,50 [°C]`), Relative Humidity (z.B. `33,10 [%]`)

### Seite 2 — Range ±10V (Kanäle 1–8)
Tabelle mit 8 Spannungspunkten (Spalten): -10,0 / -7,5 / -5,0 / -2,5 / 2,5 / 5,0 / 7,5 / 10,0 V
Zeilen:
- `Calibration Voltage (2) [V]` — Sollspannung (Referenz/DVM)
- `Tolerance [V]`, `MU U95 (1) [V]`
- Pro Kanal 1–8: `Error ChannelX [V]` (die relevante Zeile!) + `Tolerance Usage ChX [%]`

Accuracy Spec ±10V: `0,010 % Reading + 0,015 % Range`

### Seite 3 — Range ±20V (Kanal 9) und Range ±75V (Kanal 10)
- ±20V: 7 Punkte (3/6/9/12/15/18/20 V), `Error Channel9 [V]`
- ±75V: 7 Punkte (6/12/24/36/48/60/75 V), `Error Channel10 [V]`
- Accuracy Spec beide: `0,500 % Reading + 0,200 % Range`

**WICHTIG — nur diese Daten werden extrahiert:** die `Calibration Voltage`-Zeile je Range
und die `Error ChannelX`-Zeilen. Tolerance/MU/Tolerance-Usage werden NICHT für die
Linearitätsbewertung gebraucht.

---

## 2. KERN-BERECHNUNG: Datenfluss & Formeln

### Schritt A — Reading rekonstruieren
Der X-Meter-Messwert (Sample/Reading) wird aus Sollspannung + Fehler rekonstruiert:

    Reading[i] = CalibrationVoltage[i] + ErrorChannel[i]

(Reference = CalibrationVoltage bleibt der x-Wert; Reading = y-Wert der Regression.)

### Schritt B — Lineare Regression je Kanal (Reading y gegen Reference x)
Nach US-EPA **§ 1065.307** Linearity Verification. Vier Kenngrößen:

| Kenngröße        | Excel-Formel                                              |
|------------------|-----------------------------------------------------------|
| a1 (Slope)       | `SLOPE(Sample, Reference)`                                 |
| Interception     | `ABS( INDEX(Ref, MATCH(MIN(AbsRef),AbsRef,0),1)*(a1-1) + INTERCEPT(Sample,Ref) )` |
| SEE              | `STEYX(Sample, Reference)`                                 |
| r²               | `CORREL(Sample, Reference)^2`                             |

- `AbsRef` = Spalte mit `ABS(Reference)` je Punkt.
- Interception nutzt den **vorzeichenbehafteten** Referenzwert am Index des
  kleinsten Absolutwerts (nicht `MIN(ABS)`!). Das ist entscheidend für Bit-Genauigkeit,
  wenn a1 leicht von 1 abweicht.

### Schritt C — Grenzwerte (aus EPA-Tabelle, Zeile "Voltage")
Skalierung mit `max(|Reference|)` des jeweiligen Kanals:

| Kenngröße     | Grenzwert                          |
|---------------|-------------------------------------|
| a1            | 0,98 ≤ a1 ≤ 1,02  (=1 ± 0,02)      |
| Interception  | ≤ 0,01 · max(\|Ref\|)              |
| SEE           | ≤ 0,02 · max(\|Ref\|)              |
| r²            | ≥ 0,99                             |

Daraus konkret:
- ±10V: Interc. ≤ 0,1 ; SEE ≤ 0,2
- ±20V: Interc. ≤ 0,2 ; SEE ≤ 0,4
- ±75V: Interc. ≤ 0,75 ; SEE ≤ 1,5

### Schritt D — Test State
    PASSED  wenn (Anzahl Punkte ≥ 3) UND alle vier Kriterien erfüllt
    FAILED  sonst

Excel: `=IF(AND(COUNT(idx)>=3, a1>=min, a1<=max, interc<=max, SEE<=max, r2>=min),"PASSED","FAILED")`

---

## 3. OUTPUT A: Excel-Bewertungsdokument (.xlsx)

Blattstruktur (14 Sheets):
1. `Cal-Info` — alle Stammdaten (Serial, Report ID, Cal-Datum, DVM-Daten, Messbedingungen, Notes)
2. `Summary` — Übersicht aller 10 Kanäle: a1, |Interc.|, SEE, r² + Grenzwerte + PASSED/FAILED
3. `References` — EPA-Grenzwerttabelle (15 Systeme, Zeile "Voltage" wird per VLOOKUP genutzt)
4. `X-Meter CAL PROTOCOL` — Umrechnung: Reading = Volt + Error; TRANSPOSE horizontal→vertikal
5. `±10V CH1` … `±10V CH8`, `±20V CH9`, `±75V CH10` — je eine volle Bewertung

Pro Kanal-Sheet:
- Kopf: "Linearity Verification - <Range (CHx)>"
- Blöcke: Test Data / Reference Device Data / Test Results (4 Kenngrößen + Test State)
- Datentabelle: Index | Reference [V] | Sample [V] | Dev. [V] | Dev. [%] | (Abs(ref) Hilfsspalte G)
- Sample-Spalte referenziert die Reading-Werte aus `X-Meter CAL PROTOCOL`

---

## 4. OUTPUT B: PDF im AVL-Stil (10 Seiten, 1 pro Kanal)

Layout je Seite:
- Titel links: "Linearity Verification - Voltage" (Helvetica 20pt)
- AVL-Logo rechts oben (aus Zertifikat extrahierbar via PyMuPDF, ~826×354 px)
- 3 blaue Section-Bars (Farbe RGB 0x4F81BD): "Test Data", "Reference Device Data", "Test Results"
- Gelbe Datenfelder (RGB FFFF00) für befüllte Werte
- Test-Results-Tabelle: Description | Calculated | Limits; Test-State-Zelle grün (0x92D050) bei PASSED, rot (FF0000) bei FAILED
- Datentabelle 16 Zeilen (Rest leer), Reference+Sample-Spalten gelb, Kopf grau
- Notes-Box unten: "Notes: Linearity Check Version 3.0" + GPN/Document No/SAP/Change No/Revision

Feste Textfelder (nicht aus Zertifikat, im Report konstant):
- Order / Device: `SEMA / X-Meter`
- Legislation: `§ 1065.307 Linearity verification. - [79 FR 23766, Apr. 28, 2014]`
- Reference Device Description: `Fluke 8588A DVM digital voltage meter`
- DVM Serial: `PM` + Gage No (z.B. `PM1393`)
- DVM Instrument Range: `100 mV to 1000 V`

Deutsche Zahlenformatierung im PDF: Dezimal-Komma statt Punkt.

---

## 5. Tech-Stack
- **Python** mit `openpyxl` (Excel), `reportlab` (PDF), `pymupdf` (PDF-Parsing + Logo-Extraktion)
- PDF-Textextraktion: `pymupdf` (get_text) für die Tabellenwerte, mit Validierungs-/
  Bestätigungsschritt (Werte sind sicherheitskritisch!)
- Excel-Formeln müssen mit LibreOffice `soffice --headless` neu berechnet werden, damit
  TRANSPOSE-Arrays und VLOOKUPs Werte liefern.

## 6. Validierung (PFLICHT)
- Nach Berechnung: berechnete a1/Interc./SEE/r² gegen ggf. vorhandenes Referenz-PDF prüfen.
- Toleranz für Bit-Vergleich: < 2e-6.
- Bei extrahierten Werten: Plausibilitätscheck (Anzahl Punkte, Vorzeichen, Wertebereich).
- Rechtlicher Hinweis im/zum Report: Werteübertragung durch PM, keine Haftung für
  Richtigkeit; Logik/Formeln validiert; vor Kundenfreigabe prüfen.

## 7. Dateibenennung
- Excel: `SAO_abs_Linearity_Verification_X-Meter_SN_<serial>.xlsx`
- PDF:   `SAO_abs_Linearity_Verification_X-Meter_SN_<serial>.pdf`
