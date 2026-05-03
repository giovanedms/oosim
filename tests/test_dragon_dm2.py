"""Tests for Crew Dragon DM-2 scenario."""
import numpy as np
import pytest

from oosim.scenarios.dragon_dm2 import make_dragon_dm2_scenario, DM2_THRUST_ACCEL, DM2_INERTIA
from oosim.validation import validate_mission, ValidationTier


def test_dm2_scenario_well_formed():
    s = make_dragon_dm2_scenario()
    assert s.chaser_initial_eci.shape == (6,)
    assert s.target_initial_eci.shape == (6,)
    assert s.tier == ValidationTier.TIER_B
    assert s.inertia.shape == (3, 3)
    assert s.thrust_acceleration == DM2_THRUST_ACCEL


def test_dm2_pipeline_runs_end_to_end():
    rep = validate_mission(make_dragon_dm2_scenario())
    assert rep is not None
    assert rep.result.total_dv_m_s > 0
    assert rep.result.terminal_distance_m < 1000.0


def test_dm2_references_include_nasa_or_spacex():
    s = make_dragon_dm2_scenario()
    refs_text = " ".join(s.references).lower()
    assert "nasa" in refs_text or "spacex" in refs_text or "dragon" in refs_text
