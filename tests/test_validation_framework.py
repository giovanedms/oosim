"""Tests for the F3-real mission validation framework."""
import numpy as np
import pytest

from oosim.validation import (
    MissionScenario, ValidationTier, MissionRunResult,
    ValidationReport, validate_mission,
)
from oosim.validation.mission_runner import run_mission, _TOLERANCE_BY_TIER
from oosim.scenarios.atv1 import make_atv1_scenario


def test_tolerances_defined_for_all_tiers():
    for tier in ValidationTier:
        assert tier in _TOLERANCE_BY_TIER


def test_tier_A_tolerance_tighter_than_tier_B():
    a_dv, _ = _TOLERANCE_BY_TIER[ValidationTier.TIER_A]
    b_dv, _ = _TOLERANCE_BY_TIER[ValidationTier.TIER_B]
    assert a_dv < b_dv


def test_atv1_scenario_well_formed():
    s = make_atv1_scenario()
    assert s.chaser_initial_eci.shape == (6,)
    assert s.target_initial_eci.shape == (6,)
    assert s.tier == ValidationTier.TIER_B
    assert s.inertia.shape == (3, 3)


def test_run_mission_returns_complete_result():
    s = make_atv1_scenario()
    res = run_mission(s)
    assert isinstance(res, MissionRunResult)
    assert res.total_dv_m_s > 0
    assert res.total_duration_s > 0
    assert res.terminal_distance_m >= 0


def test_validate_mission_returns_report_with_summary():
    s = make_atv1_scenario()
    rep = validate_mission(s)
    assert isinstance(rep, ValidationReport)
    assert "ATV-1" in rep.summary
    assert "Tier B" in rep.summary or "Tier_B" in rep.summary or "(Tier B)" in rep.summary


def test_validation_assertion_uses_correct_tolerance():
    s = make_atv1_scenario()
    rep = validate_mission(s)
    expected_tol = _TOLERANCE_BY_TIER[ValidationTier.TIER_B][0]
    assert rep.tolerance_dv == expected_tol
