"""Tests for M8 phasing-orbit drift loop."""
import numpy as np
import pytest

from oosim.scenarios.phasing_drift import (
    PhasingDriftPlan, compute_phasing_burns, measure_phase_angle_deg,
)
from oosim.proxops.coupled_state import MU_EARTH

R_E = 6378.137
SOYUZ_THRUST_ACCEL = 5.6e-5    # km/s²


def make_circular(altitude_km, true_anomaly_deg=0.0):
    a = R_E + altitude_km
    v = np.sqrt(MU_EARTH / a)
    th = np.radians(true_anomaly_deg)
    r = a * np.array([np.cos(th), np.sin(th), 0.0])
    vv = v * np.array([-np.sin(th), np.cos(th), 0.0])
    return np.concatenate([r, vv])


def test_phase_angle_zero_when_aligned():
    s = make_circular(420.0, 30.0)
    assert abs(measure_phase_angle_deg(s, s)) < 1e-9


def test_phase_angle_positive_when_chaser_ahead():
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, 5.0)   # 5° ahead in true anomaly
    val = measure_phase_angle_deg(chaser, target)
    assert 4.5 < val < 5.5


def test_phase_angle_negative_when_chaser_behind():
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, -5.0)
    val = measure_phase_angle_deg(chaser, target)
    assert -5.5 < val < -4.5


def test_phasing_drift_brings_chaser_close():
    """Chaser 5° behind target should end up within 5 km after k=2 phasing orbits."""
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, -5.0)
    plan = compute_phasing_burns(chaser, target, SOYUZ_THRUST_ACCEL, n_phase_orbits=2)
    assert isinstance(plan, PhasingDriftPlan)
    assert plan.relative_distance_final_m < 5000.0    # < 5 km
    assert len(plan.burns) == 2


def test_burns_are_opposite_sign():
    """Burn 2 magnitude equals burn 1 magnitude (re-circularisation)."""
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, -3.0)
    plan = compute_phasing_burns(chaser, target, SOYUZ_THRUST_ACCEL, n_phase_orbits=2)
    m1 = plan.burns[0].dv_magnitude_impulsive
    m2 = plan.burns[1].dv_magnitude_impulsive
    assert abs(m1 - m2) < 1e-9


def test_drift_time_equals_k_phasing_periods():
    """drift_time must equal k × T_phase (consistency check)."""
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, -2.0)
    plan = compute_phasing_burns(chaser, target, SOYUZ_THRUST_ACCEL, n_phase_orbits=3)
    a_target = R_E + 420.0
    T_target = 2 * np.pi * np.sqrt(a_target**3 / MU_EARTH)
    dtheta = np.radians(-2.0)
    # Vallado §6.6.1: T_phase = T_target * (1 + Δθ/(2π·k))
    # chaser is behind (dtheta < 0) → T_phase < T_target → smaller, faster orbit
    T_phase_expected = T_target * (1 + dtheta / (2 * np.pi * 3))
    assert abs(plan.drift_time - 3 * T_phase_expected) / plan.drift_time < 1e-6


def test_zero_phase_returns_zero_dv():
    """If chaser is already aligned with target, burns should be ~zero."""
    target = make_circular(420.0, 0.0)
    chaser = make_circular(420.0, 0.0)
    plan = compute_phasing_burns(chaser, target, SOYUZ_THRUST_ACCEL, n_phase_orbits=2)
    assert plan.burns[0].dv_magnitude_impulsive < 1e-6
    assert plan.burns[1].dv_magnitude_impulsive < 1e-6
