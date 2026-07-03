"""Tests for the Izzo (2015) Lambert solver.

Ground truth: exact Kepler propagation (universal variables, Vallado Alg. 8).
A state (r1, v1_true) is propagated for dt to obtain (r2, v2_true); the
Lambert solution between r1 and r2 with tof = dt must reproduce v1_true and
v2_true. A None result is a FAILURE, never silently skipped.
"""
import numpy as np
import pytest

from oosim.proxops.eci_propagator import propagate_kepler
from oosim.utils.lambert import lambert_battin
from oosim.utils.lambert_izzo import lambert_izzo, _x2tof

MU = 398600.4418
R_E = 6378.137
TOL_V = 1e-6  # km/s

A_LEO = R_E + 500.0
V_CIRC = np.sqrt(MU / A_LEO)
PERIOD_LEO = 2 * np.pi * np.sqrt(A_LEO ** 3 / MU)

RP_ECC = R_E + 300.0
E_ECC = 0.4
VP_ECC = np.sqrt(MU * (1 + E_ECC) / RP_ECC)

R_HYP = R_E + 400.0
V_HYP = 1.3 * np.sqrt(2 * MU / R_HYP)  # 1.3 x escape speed -> hyperbolic

INC = np.radians(51.6)

# (label, state0 [km, km/s], dt [s], prograde)
CASES = [
    ("leo_circular_1000s",
     [A_LEO, 0., 0., 0., V_CIRC, 0.], 1000.0, True),
    ("leo_circular_90deg",
     [A_LEO, 0., 0., 0., V_CIRC, 0.], 0.25 * PERIOD_LEO, True),
    ("leo_circular_beyond_180deg",
     [A_LEO, 0., 0., 0., V_CIRC, 0.], 0.7 * PERIOD_LEO, True),
    ("leo_circular_retrograde",
     [A_LEO, 0., 0., 0., -V_CIRC, 0.], 1000.0, False),
    ("eccentric_e04_from_perigee",
     [RP_ECC, 0., 0., 0., VP_ECC, 0.], 2000.0, True),
    ("inclined_51_6deg",
     [A_LEO, 0., 0., 0., V_CIRC * np.cos(INC), V_CIRC * np.sin(INC)],
     1200.0, True),
    ("hyperbolic",
     [R_HYP, 0., 0., 0., V_HYP, 0.], 1500.0, True),
]

# Subset where lambert_battin also converges (it returns None for transfer
# angles > 180 deg and near-parabolic geometries).
CROSS_CHECK_CASES = [c for c in CASES if c[0] not in
                     ("leo_circular_beyond_180deg",)]


def _propagate_pair(state0, dt):
    state0 = np.asarray(state0, dtype=float)
    state1 = propagate_kepler(state0, dt, mu=MU)
    return state0[:3], state0[3:], state1[:3], state1[3:]


@pytest.mark.parametrize("label,state0,dt,prograde", CASES,
                         ids=[c[0] for c in CASES])
def test_lambert_izzo_matches_kepler_propagation(label, state0, dt, prograde):
    """v1/v2 must match the exact Kepler-propagated state to <= 1e-6 km/s."""
    r1, v1_true, r2, v2_true = _propagate_pair(state0, dt)
    result = lambert_izzo(r1, r2, dt, mu=MU, prograde=prograde)
    assert result is not None, f"lambert_izzo returned None for {label}"
    v1, v2 = result
    assert np.linalg.norm(v1 - v1_true) <= TOL_V
    assert np.linalg.norm(v2 - v2_true) <= TOL_V


@pytest.mark.parametrize("label,state0,dt,prograde", CROSS_CHECK_CASES,
                         ids=[c[0] for c in CROSS_CHECK_CASES])
def test_lambert_izzo_agrees_with_battin(label, state0, dt, prograde):
    """Cross-check against the universal-variable solver on the same cases."""
    r1, _, r2, _ = _propagate_pair(state0, dt)
    res_izzo = lambert_izzo(r1, r2, dt, mu=MU, prograde=prograde)
    res_battin = lambert_battin(r1, r2, dt, mu=MU, prograde=prograde)
    assert res_izzo is not None, f"lambert_izzo returned None for {label}"
    assert res_battin is not None, f"lambert_battin returned None for {label}"
    assert np.linalg.norm(res_izzo[0] - res_battin[0]) <= TOL_V
    assert np.linalg.norm(res_izzo[1] - res_battin[1]) <= TOL_V


def test_x2tof_consistent_with_initial_guess_anchor():
    """Regression: T(x=0, ll) must equal T0 = arccos(ll) + ll*sqrt(1-ll^2).

    The broken v1 implementation returned _x2tof(0, 0) = 0.5708 while the
    initial guess used T0 = pi/2 = 1.5708, so the iteration chased the wrong
    curve and never converged.
    """
    for ll in (-0.9, -0.5, 0.0, 0.3, 0.7, 0.95):
        T0 = np.arccos(ll) + ll * np.sqrt(1.0 - ll * ll)
        assert abs(_x2tof(0.0, ll) - T0) < 1e-12


def test_x2tof_parabolic_point():
    """T(x=1, ll) = 2/3 * (1 - ll^3) exactly (Izzo eq. for the parabola)."""
    for ll in (-0.9, 0.0, 0.5, 0.95):
        assert abs(_x2tof(1.0, ll) - (2.0 / 3.0) * (1.0 - ll ** 3)) < 1e-12


def test_lambert_izzo_rejects_zero_tof():
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = np.array([R_E + 300., 100., 0.])
    assert lambert_izzo(r1, r2, 0.0) is None


def test_lambert_izzo_rejects_collinear_180deg():
    """Transfer plane is undefined for r2 = -k*r1; must return None."""
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = -r1
    tof = np.pi * np.sqrt((R_E + 300.) ** 3 / MU)
    assert lambert_izzo(r1, r2, tof) is None
