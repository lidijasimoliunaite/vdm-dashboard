"""Sugeneruoja vieną savarankišką index.html iš JSON duomenų ir Jinja šablono."""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import TRACK_TYPES, Dashboard, load

log = logging.getLogger(__name__)
PKG = Path(__file__).parent


def fmt_num(value, decimals: int = 0) -> str:
    """Skaičius be tūkstančių skyriklių: 3588.1, 4071."""
    if value is None:
        return "—"
    return f"{value:.{decimals}f}"


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(PKG / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["num"] = fmt_num
    return env


def render(dash: Dashboard) -> str:
    css = (PKG / "static" / "style.css").read_text(encoding="utf-8")
    js = (PKG / "static" / "app.js").read_text(encoding="utf-8")
    return _env().get_template("index.html").render(
        d=dash,
        track_types=TRACK_TYPES,
        css=css,
        js=js,
        data_json=json.dumps(dash.to_js(), ensure_ascii=False),
        build_date=date.today().isoformat(),
    )


def export_csv(dash: Dashboard, out_dir: Path) -> Path:
    path = out_dir / "kryptys.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kodas", "pavadinimas", *[k for k, *_ in TRACK_TYPES], "viso_km",
                    "iesmai", "sviesoforai", "vdm_main_km", "gips_km", "skirtumas_km"])
        for ln in dash.directions:
            w.writerow([ln.code, ln.name, *[getattr(ln, k) for k, *_ in TRACK_TYPES], ln.total_km,
                        ln.switches, ln.signals, ln.vdm_main_exact, ln.gips, ln.gips_diff])
    return path


def build(data_path: Path, out_dir: Path, csv_out: bool = True) -> Path:
    dash = load(data_path)

    for w in dash.warnings:
        log.warning(w)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(render(dash), encoding="utf-8")
    if csv_out:
        export_csv(dash, out_dir)
    return out
