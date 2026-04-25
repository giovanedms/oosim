"""Tests for mission reference data parsers."""
from oosim.missions import (
    SOYUZ_MS17, APOLLO11_LM_RDV, ATV1_JULES_VERNE, HTV7_KOUNOTORI, ALL_MISSIONS
)


def test_all_missions_have_required_fields():
    for m in ALL_MISSIONS:
        assert m.mission_id
        assert m.launch_utc
        assert m.dock_utc
        assert m.launch_to_dock_min > 0
        assert m.target_port
        assert m.gnc_system
        assert m.capture_mechanism
        assert m.granularity in {"HIGH", "MEDIUM", "LOW"}


def test_soyuz_ms17_burn_total_matches():
    """Per-burn dv must sum to published total within 1 m/s."""
    s = sum(b.delta_v_ms for b in SOYUZ_MS17.burns)
    assert abs(s - SOYUZ_MS17.total_dv_ms) < 1.0


def test_apollo11_lor_profile():
    """Apollo 11 LOR has 5 burns including the 1687 m/s ascent insertion."""
    assert len(APOLLO11_LM_RDV.burns) == 5
    insert = APOLLO11_LM_RDV.burns[0]
    assert insert.name == "INSERT"
    assert insert.delta_v_ms > 1500


def test_atv1_aggregate_only():
    """ATV-1 has aggregate-only data (per-burn dv not public)."""
    assert ATV1_JULES_VERNE.total_dv_ms == 0.0
    for b in ATV1_JULES_VERNE.burns:
        assert b.delta_v_ms == 0.0


def test_htv7_long_phasing():
    """HTV-7 berthing took ~5 days; ensure ballpark."""
    days = HTV7_KOUNOTORI.launch_to_dock_min / 60.0 / 24.0
    assert 4.0 < days < 6.0
