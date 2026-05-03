"""Tests for M7 Soyuz MS-17 end-to-end smoke pipeline."""
import numpy as np
import pytest

from oosim.scenarios.soyuz_ms17 import (
    run_soyuz_ms17_pipeline, report, SoyuzMS17Result,
    make_iss_state, make_soyuz_insertion_state,
)


def test_pipeline_runs_end_to_end():
    """Default placeholders run without error and produce a SoyuzMS17Result."""
    res = run_soyuz_ms17_pipeline()
    assert isinstance(res, SoyuzMS17Result)
    assert res.phasing_plan is not None
    assert res.terminal_result is not None


def test_phasing_dv_in_physically_reasonable_range():
    """Two-impulse Hohmann 200→420 km should give ~110-150 m/s impulsive total."""
    res = run_soyuz_ms17_pipeline()
    dv = res.phasing_plan.total_dv_impulsive * 1000.0  # m/s
    assert 100.0 < dv < 160.0, f"phasing Δv = {dv:.1f} m/s outside [100, 160]"


def test_terminal_distance_converges():
    """MPC should bring chaser within 50 m of envelope center."""
    res = run_soyuz_ms17_pipeline()
    assert res.terminal_distance_m < 50.0, \
        f"terminal distance {res.terminal_distance_m:.1f} m exceeds 50 m"


def test_total_dv_in_smoke_envelope():
    """Total Δv (phasing + drift + terminal) within ample [50, 400] m/s envelope."""
    res = run_soyuz_ms17_pipeline()
    assert 50.0 < res.total_dv_m_s < 400.0, \
        f"total Δv = {res.total_dv_m_s:.1f} m/s outside envelope"


def test_report_string_contains_key_sections():
    """Sanity-check the textual report."""
    res = run_soyuz_ms17_pipeline()
    txt = report(res)
    assert "Phasing" in txt
    assert "Terminal" in txt
    assert "Murtazin" in txt
    assert "Total Δv" in txt


def test_make_iss_state_returns_circular_orbit():
    """ISS placeholder should be circular at the requested altitude."""
    s = make_iss_state(altitude_km=420.0)
    r = float(np.linalg.norm(s[:3]))
    assert abs(r - (6378.137 + 420.0)) < 1.0


def test_pipeline_includes_phasing_drift():
    """Result should expose phasing_drift_plan and reduce relative distance."""
    res = run_soyuz_ms17_pipeline()
    assert res.phasing_drift_plan is not None
    # Distance after M8 drift should be MUCH less than after Hohmann alone
    assert res.phasing_drift_plan.relative_distance_final_m < 100_000  # < 100 km
