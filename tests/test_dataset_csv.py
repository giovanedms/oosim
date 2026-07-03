"""Integrity checks for the RPOD-50 dataset CSV (missions.csv)."""
import csv
from datetime import datetime

import pytest

from oosim.validation.flight_data import resolve_dataset_path

try:
    CSV_PATH = resolve_dataset_path()
except FileNotFoundError:
    CSV_PATH = None

pytestmark = pytest.mark.skipif(
    CSV_PATH is None, reason="RPOD-50 dataset not found (see OOSIM_DATASET_DIR)"
)

N_COLUMNS = 19
N_MISSIONS = 50


def _read_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_row_count_and_column_count():
    rows = _read_rows()
    assert len(rows) == N_MISSIONS + 1  # header + 50 missions
    for i, row in enumerate(rows):
        assert len(row) == N_COLUMNS, f"line {i + 1} has {len(row)} columns"


def test_mission_ids_unique():
    rows = _read_rows()
    ids = [row[0] for row in rows[1:]]
    assert len(ids) == len(set(ids)), "duplicate mission_id found"


def test_year_and_launch_utc_parseable():
    rows = _read_rows()
    header = rows[0]
    yi = header.index("year")
    li = header.index("launch_utc")
    for row in rows[1:]:
        year = int(row[yi])  # raises ValueError if not an int
        assert 1960 <= year <= 2100
        launch = datetime.strptime(row[li], "%Y-%m-%dT%H:%M:%SZ")
        assert launch.year <= year + 1  # launch precedes (or equals) event year


def test_soyuz4_5_internal_comma_quoted():
    rows = _read_rows()
    header = rows[0]
    by_id = {row[0]: row for row in rows[1:]}
    row = by_id["SOYUZ4_5"]
    gnc = row[header.index("gnc_system")]
    assert gnc == "Igla (auto until ~100m, manual after)"
    assert row[header.index("granularity")] == "MEDIUM"
    assert row[header.index("capture_mechanism")] == (
        "hard-dock probe-drogue (no internal tunnel)"
    )
