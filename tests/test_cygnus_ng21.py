"""Tests for Cygnus NG-21 scenario."""
import numpy as np
import pytest

from oosim.scenarios.cygnus_ng21 import make_cygnus_ng21_scenario, NG21_THRUST_ACCEL, NG21_INERTIA
from oosim.validation import validate_mission, ValidationTier


def test_ng21_scenario_well_formed():
    s = make_cygnus_ng21_scenario()
    assert s.chaser_initial_eci.shape == (6,)
    assert s.target_initial_eci.shape == (6,)
    assert s.tier == ValidationTier.TIER_B
    assert s.inertia.shape == (3, 3)
    assert s.thrust_acceleration == NG21_THRUST_ACCEL


def test_ng21_pipeline_runs_end_to_end():
    rep = validate_mission(make_cygnus_ng21_scenario())
    assert rep is not None
    assert rep.result.total_dv_m_s > 0
    assert rep.result.terminal_distance_m < 1000.0


def test_ng21_references_include_nasa_or_northrop():
    s = make_cygnus_ng21_scenario()
    refs_text = " ".join(s.references).lower()
    assert "nasa" in refs_text or "northrop" in refs_text or "cygnus" in refs_text
