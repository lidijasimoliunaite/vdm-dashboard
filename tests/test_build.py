from pathlib import Path

import pytest

from gits_dashboard.__main__ import main
from gits_dashboard.build import build, fmt_num
from gits_dashboard.models import load

DATA = Path(__file__).parents[1] / "data" / "dashboard.json"


@pytest.fixture(scope="module")
def dash():
    return load(DATA)


def test_all_25_directions(dash):
    assert len(dash.directions) == 25
    assert all(code.startswith("L") for code in dash.lines if code != "ALL")


def test_track_types_sum_to_network_total(dash):
    total = sum(ln.total_km for ln in dash.directions)
    assert total == pytest.approx(dash.lines["ALL"].total_km, abs=1.0)


def test_digitization_rows_are_percentages(dash):
    for row in dash.digitization:
        assert row["done"] + row["in_progress"] + row["postponed"] == 100


def test_gips_diff(dash):
    assert dash.lines["L21"].gips_diff == 0
    assert dash.lines["L02"].gips_diff is None
    assert dash.lines["L03"].gips_diff == pytest.approx(43.587)


def test_numbers_have_no_thousand_separators():
    assert fmt_num(3588.1, 1) == "3588.1"
    assert fmt_num(4071) == "4071"
    assert fmt_num(None) == "—"


def test_build_writes_html_and_csv(tmp_path):
    out = build(DATA, tmp_path)
    html = out.read_text(encoding="utf-8")
    assert "<title>GITS" in html
    assert "window.GITS_DATA" in html
    assert 'value="L25"' in html
    assert "{{" not in html  # nėra neišrenderintų Jinja žymų
    csv_lines = (tmp_path / "kryptys.csv").read_text(encoding="utf-8").splitlines()
    assert len(csv_lines) == 26  # antraštė + 25 kryptys


def test_cli_check_runs():
    assert main(["check", "--data", str(DATA)]) == 0
