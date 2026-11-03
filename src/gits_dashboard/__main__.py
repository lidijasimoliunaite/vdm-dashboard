"""CLI: python -m gits_dashboard [build|check|serve]"""

from __future__ import annotations

import argparse
import functools
import http.server
import logging
import sys
from pathlib import Path

from .build import build
from .models import load

DEFAULT_DATA = Path("data/dashboard.json")
DEFAULT_OUT = Path("dist")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="gits-dashboard", description="GITS Kelių ūkio statistikos skydelis")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="sugeneruoti dist/index.html")
    b.add_argument("--data", type=Path, default=DEFAULT_DATA)
    b.add_argument("--out", type=Path, default=DEFAULT_OUT)
    b.add_argument("--no-csv", action="store_true")

    c = sub.add_parser("check", help="patikrinti duomenų nuoseklumą")
    c.add_argument("--data", type=Path, default=DEFAULT_DATA)
    c.add_argument("--strict", action="store_true", help="grąžinti klaidą, jei yra įspėjimų")

    s = sub.add_parser("serve", help="peržiūra naršyklėje (http://localhost:8000)")
    s.add_argument("--out", type=Path, default=DEFAULT_OUT)
    s.add_argument("--port", type=int, default=8000)

    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    if a.cmd == "build":
        out = build(a.data, a.out, csv_out=not a.no_csv)
        print(f"✓ {out}")
        return 0

    if a.cmd == "check":
        d = load(a.data)
        for w in d.warnings:
            print(f"⚠ {w}")
        print(f"{len(d.directions)} kryptys, {len(d.warnings)} įspėjimai")
        return 1 if (a.strict and d.warnings) else 0

    if a.cmd == "serve":
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(a.out))
        print(f"http://localhost:{a.port}")
        http.server.ThreadingHTTPServer(("", a.port), handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
