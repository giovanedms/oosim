"""Tests for HTV-7 Kounotori scenario."""
import numpy as np
import pytest

from oosim.scenarios.htv7 import make_htv7_scenario, HTV7_THRUST_ACCEL, HTV7_INERTIA
from oosim.validation import validate_mission, ValidationTier


def test_htv7_scenario_well_formed():
    s = make_htv7_scenario()
    assert s.chaser_initial_eci.shape == (6,)
    assert s.target_initial_eci.shape == (6,)
    assert s.tier == ValidationTier.TIER_B
    assert s.inertia.shape == (3, 3)
    assert s.thrust_acceleration == HTV7_THRUST_ACCEL


def test_htv7_pipeline_runs_end_to_end():
    """The full M5+M8+M9+M6 pipeline runs without exception."""
    rep = validate_mission(make_htv7_scenario())
    assert rep is not None
    assert rep.result.total_dv_m_s > 0
    assert rep.result.terminal_distance_m < 1000.0  # less than 1 km after pipeline


def test_htv7_references_include_jaxa():
    s = make_htv7_scenario()
    refs_text = " ".join(s.references).lower()
    assert "jaxa" in refs_text or "htv" in refs_text
