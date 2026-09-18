"""Shared per-channel/sheet layout, used by both build_xlsx.py and
extract_results.py so the two stay in sync (sheet names, data-row offsets).
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import CalibrationData, RangeData

# First data row of the results table on every channel sheet (see
# reference_build_xlsx.py make_channel: d1=28).
DATA_START_ROW = 28


@dataclass(frozen=True)
class ChannelSpec:
    sheet: str  # e.g. '±10V CH1'
    range_label: str  # e.g. '±10V (CH1)' -- shown as "Instrument Range:"
    channel: int  # 1..10
    range_key: str  # 'r10' | 'r20' | 'r75'

    def range_data(self, data: CalibrationData) -> RangeData:
        return getattr(data, self.range_key)

    def npts(self, data: CalibrationData) -> int:
        return len(self.range_data(data).voltages)


def channel_specs() -> list[ChannelSpec]:
    specs = [
        ChannelSpec(sheet=f"±10V CH{ch}", range_label=f"±10V (CH{ch})", channel=ch, range_key="r10")
        for ch in range(1, 9)
    ]
    specs.append(ChannelSpec(sheet="±20V CH9", range_label="±20V (CH9)", channel=9, range_key="r20"))
    specs.append(ChannelSpec(sheet="±75V CH10", range_label="±75V (CH10)", channel=10, range_key="r75"))
    return specs
