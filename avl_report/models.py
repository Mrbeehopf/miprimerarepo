"""Data model for one AVL X-Meter calibration certificate.

Mirrors the structure of the reference `reference_data_example.py` module
(see SPEC.md), but as a JSON-serializable dataclass instead of a hardcoded
Python module, so a certificate's data can be extracted, reviewed, edited
and stored per-run instead of being baked into source code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class RangeData:
    label: str  # e.g. '±10V', '±20V', '±75V'
    accuracy_spec: str
    voltages: List[float]  # Calibration Voltage (2) [V], per data point
    errors: Dict[int, List[float]]  # channel number -> Error ChannelX [V], per data point

    def to_dict(self) -> dict:
        d = asdict(self)
        d["errors"] = {str(k): v for k, v in self.errors.items()}
        return d

    @staticmethod
    def from_dict(d: dict) -> "RangeData":
        return RangeData(
            label=d["label"],
            accuracy_spec=d["accuracy_spec"],
            voltages=[float(v) for v in d["voltages"]],
            errors={int(k): [float(v) for v in vs] for k, vs in d["errors"].items()},
        )


@dataclass
class CalibrationData:
    calibration_date: str
    report_id: str
    device: str
    serial_no: str
    dvm_manufacturer: str
    dvm_type: str
    dvm_gage_no: str
    dvm_calibration_date: str
    ambient_temperature: str
    relative_humidity: str
    r10: RangeData  # channels 1-8, range +/-10V
    r20: RangeData  # channel 9, range +/-20V
    r75: RangeData  # channel 10, range +/-75V

    @property
    def info(self) -> dict:
        """Header dict, matching the `INFO` dict shape of the reference script."""
        return {
            "Calibration Date": self.calibration_date,
            "Report ID": self.report_id,
            "Device": self.device,
            "Serial No": self.serial_no,
            "DVM Manufacturer": self.dvm_manufacturer,
            "DVM Type": self.dvm_type,
            "DVM Gage No": self.dvm_gage_no,
            "DVM Calibration Date": self.dvm_calibration_date,
            "Ambient Temperature": self.ambient_temperature,
            "Relative Humidity": self.relative_humidity,
        }

    def to_dict(self) -> dict:
        return {
            "calibration_date": self.calibration_date,
            "report_id": self.report_id,
            "device": self.device,
            "serial_no": self.serial_no,
            "dvm_manufacturer": self.dvm_manufacturer,
            "dvm_type": self.dvm_type,
            "dvm_gage_no": self.dvm_gage_no,
            "dvm_calibration_date": self.dvm_calibration_date,
            "ambient_temperature": self.ambient_temperature,
            "relative_humidity": self.relative_humidity,
            "r10": self.r10.to_dict(),
            "r20": self.r20.to_dict(),
            "r75": self.r75.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "CalibrationData":
        return CalibrationData(
            calibration_date=str(d["calibration_date"]),
            report_id=str(d["report_id"]),
            device=str(d["device"]),
            serial_no=str(d["serial_no"]),
            dvm_manufacturer=str(d["dvm_manufacturer"]),
            dvm_type=str(d["dvm_type"]),
            dvm_gage_no=str(d["dvm_gage_no"]),
            dvm_calibration_date=str(d["dvm_calibration_date"]),
            ambient_temperature=str(d["ambient_temperature"]),
            relative_humidity=str(d["relative_humidity"]),
            r10=RangeData.from_dict(d["r10"]),
            r20=RangeData.from_dict(d["r20"]),
            r75=RangeData.from_dict(d["r75"]),
        )

    def save(self, path: Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def load(path: Path) -> "CalibrationData":
        return CalibrationData.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
