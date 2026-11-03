"""Duomenų modelis: įkelia ir patikrina data/dashboard.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRACK_TYPES = [
    # (raktas JSON'e, pavadinimas, GKODAS, spalva)
    ("main", "Pagrindinis kelias", "gk_I / gk_II", "var(--green)"),
    ("siding", "Stoties kiti keliai", "gk_kt", "#2d7a50"),
    ("secondary", "Atvykimo–išvykimo keliai", "gk_ai", "#3d9966"),
    ("connecting", "Sąvažos", "gk_sv", "var(--amber)"),
    ("unknown", "GKODAS nenustatytas", "null", "var(--dim)"),
]


@dataclass
class Line:
    code: str
    name: str
    main: float
    siding: float
    secondary: float
    connecting: float
    unknown: float
    switches: int
    signals: int
    vdm_main_exact: float | None = None
    gips: float | None = None

    @property
    def total_km(self) -> float:
        return round(self.main + self.siding + self.secondary + self.connecting + self.unknown, 1)

    @property
    def gips_diff(self) -> float | None:
        if self.vdm_main_exact is None or self.gips is None:
            return None
        return round(self.vdm_main_exact - self.gips, 3)


@dataclass
class Dashboard:
    meta: dict[str, Any]
    kpi: dict[str, Any]
    lines: dict[str, Line]
    digitization: list[dict[str, Any]]
    switch_split: list[dict[str, Any]]
    tiles: list[dict[str, Any]]
    signal_types: list[dict[str, Any]]
    data_quality: list[dict[str, Any]]
    taxonomy: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    @property
    def directions(self) -> list[Line]:
        """Visos kryptys be suvestinės ALL eilutės."""
        return [ln for c, ln in self.lines.items() if c != "ALL"]

    def gips_total(self) -> float:
        return round(sum(ln.gips for ln in self.directions if ln.gips is not None), 1)

    def lines_without_gips(self) -> int:
        return sum(1 for ln in self.directions if ln.gips is None)

    def to_js(self) -> dict[str, Any]:
        """Kompaktiški duomenys, kuriuos naršyklėje naudoja filtras."""
        return {
            code: {
                "name": ln.name,
                "tracks": {k: getattr(ln, k) for k, *_ in TRACK_TYPES},
                "total": ln.total_km,
                "switches": ln.switches,
                "signals": ln.signals,
            }
            for code, ln in self.lines.items()
        }


def load(path: str | Path) -> Dashboard:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = {code: Line(code=code, **vals) for code, vals in raw["lines"].items()}
    dash = Dashboard(
        meta=raw["meta"],
        kpi=raw["kpi"],
        lines=lines,
        digitization=raw["digitization"],
        switch_split=raw["switch_split"],
        tiles=raw["tiles"],
        signal_types=raw["signal_types"],
        data_quality=raw["data_quality"],
        taxonomy=raw["taxonomy"],
    )
    dash.warnings = validate(dash)
    return dash


def validate(d: Dashboard) -> list[str]:
    """Grąžina įspėjimus apie duomenų neatitikimus (build nesustabdo)."""
    w: list[str] = []
    if "ALL" not in d.lines:
        w.append("Trūksta suvestinės eilutės 'ALL'.")
        return w

    all_line = d.lines["ALL"]
    for key, label, *_ in TRACK_TYPES:
        s = round(sum(getattr(ln, key) for ln in d.directions), 1)
        diff = abs(s - getattr(all_line, key))
        if diff > 1.0:
            w.append(f"{label}: krypčių suma {s} km ≠ ALL {getattr(all_line, key)} km (Δ {diff:.1f}).")

    for row in d.digitization:
        total = row["done"] + row["in_progress"] + row["postponed"]
        if total != 100:
            w.append(f"Skaitmenizavimas {row['label']}: procentų suma {total}, ne 100.")

    split = sum(s["value"] for s in d.switch_split)
    if split != d.kpi["switches"]:
        w.append(f"Iešmų pasiskirstymas sumoje {split} ≠ KPI {d.kpi['switches']}.")

    for ln in d.directions:
        if ln.gips_diff is not None and abs(ln.gips_diff) > 20:
            w.append(f"{ln.code} {ln.name}: VDM ir GIPS skiriasi {ln.gips_diff:+.1f} km.")
    return w
