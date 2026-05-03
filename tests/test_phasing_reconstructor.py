"""Tests for M5 mission phasing reconstructor."""
import numpy as np
import pytest
from oosim.scenarios.phasing_reconstructor import (
    reconstruct_phasing, ImpulseEvent, PhasingPlan
)
from oosim.proxops.eci_propagator import MU_EARTH

# Soyuz docking thrust: ~390 N / ~7000 kg ≈ 5.6e-5 km/s²
SOYUZ_THRUST_ACCEL = 5.6e-5

def make_circular_state(altitude_km, true_anomaly_deg=0.0):
    """Helper: build (6,) ECI state for a circular orbit at given altitude."""
    R_E = 6378.137
    a = R_E + altitude_km
    v_circ = np.sqrt(MU_EARTH / a)
    th = np.radians(true_anomaly_deg)
    r = a * np.array([np.cos(th), np.sin(th), 0.0])
    v = v_circ * np.array([-np.sin(th), np.cos(th), 0.0])
    return np.concatenate([r, v])


def test_hohmann_low_to_higher_orbit_returns_two_burns():
    """Low orbit → higher orbit: must produce 2 prograde burns."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)  # ISS-like altitude
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL)
    assert len(plan.burns) == 2
    assert plan.burns[0].label == 'perigee_raise'
    assert plan.burns[1].label == 'apogee_circularise'
    # Both burns should be prograde at their respective points
    v1 = chaser[3:6] / np.linalg.norm(chaser[3:6])
    dv1_dir = plan.burns[0].dv_eci / np.linalg.norm(plan.burns[0].dv_eci)
    assert np.dot(v1, dv1_dir) > 0.999  # nearly parallel to initial velocity


def test_hohmann_dv_matches_textbook_value():
    """Δv for 200km → 420km Hohmann transfer matches Vallado Eq. 6-7."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL)
    # Analytical: dv1 = sqrt(mu/r1)*(sqrt(2*r2/(r1+r2)) - 1)
    R_E = 6378.137
    r1, r2 = R_E + 200, R_E + 420
    v_circ_1 = np.sqrt(MU_EARTH / r1)
    dv1_analytical = v_circ_1 * (np.sqrt(2 * r2 / (r1 + r2)) - 1)
    assert abs(plan.burns[0].dv_magnitude_impulsive - dv1_analytical) < 1e-6


def test_finite_burn_correction_increases_dv():
    """Finite-burn dv must be > impulsive dv."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL)
    for b in plan.burns:
        assert b.dv_magnitude_corrected > b.dv_magnitude_impulsive
        assert b.duration > 0.0


def test_terminal_state_close_to_target_orbit():
    """After both burns, chaser must be on (or very close to) target orbit."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL, use_j2=False)
    # End-of-trajectory chaser radius should equal target altitude radius
    r_final = np.linalg.norm(plan.chaser_trajectory_x[0:3, -1])
    R_E = 6378.137
    assert abs(r_final - (R_E + 420)) < 1.0  # within 1 km


def test_lvlh_terminal_state_returned():
    """terminal_lvlh dict must contain dr_lvlh and dv_lvlh."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL)
    assert 'dr_lvlh' in plan.terminal_lvlh
    assert 'dv_lvlh' in plan.terminal_lvlh
    assert plan.terminal_lvlh['dr_lvlh'].shape == (3,)


def test_total_dv_summation():
    """total_dv must equal sum of individual burn magnitudes."""
    chaser = make_circular_state(200.0)
    target = make_circular_state(420.0)
    plan = reconstruct_phasing(chaser, target, SOYUZ_THRUST_ACCEL)
    expected_imp = sum(b.dv_magnitude_impulsive for b in plan.burns)
    assert abs(plan.total_dv_impulsive - expected_imp) < 1e-12
