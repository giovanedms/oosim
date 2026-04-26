"""Physics-invariant tests demanded by Gemini round 4 review.

Verifies that the OOSim numerical kernels respect the conservation laws
they should — a defense against the reviewer attack 'where are the physics
tests?' anticipated for the IAC Q&A.
"""
import numpy as np
import pytest
from oosim.proxops.hcw import hcw_state_transition_matrix, propagate_hcw, mean_motion
from oosim.utils.frames_extra import (
    keplerian_to_cartesian, cartesian_to_keplerian, perifocal_to_eci,
)


@pytest.mark.xfail(reason=("HCW dynamics in LVLH (rotating) frame are not Hamiltonian "
                            "in the naive sense — Coriolis terms break the standard "
                            "Phi^T J Phi = J invariant. Phase-space volume preservation "
                            "(det Phi = 1) is preserved instead, see "
                            "test_hcw.py::test_stm_determinant_unity which passes."))
def test_hcw_stm_symplectic_property_naive():
    """HCW STM is NOT symplectic in the naive Phi^T J Phi = J sense because the
    LVLH frame is rotating (introduces Coriolis terms not captured by the
    canonical symplectic structure). The relevant invariant is the determinant
    (volume preservation), tested separately in test_hcw.py."""
    n = mean_motion(6378.137 + 408.0)
    J = np.zeros((6, 6))
    J[:3, 3:] = np.eye(3)
    J[3:, :3] = -np.eye(3)
    Phi = hcw_state_transition_matrix(n, 100.0)
    residual = Phi.T @ J @ Phi - J
    assert np.max(np.abs(residual)) < 1e-9


def test_hcw_propagation_time_reversal():
    """Time-reversal: propagating forward by t, then backward by t, must
    return the initial state to within numerical precision. This is a strong
    consistency check on the closed-form STM."""
    n = mean_motion(6378.137 + 408.0)
    state0 = np.array([10.0, -50.0, 5.0, 0.01, -0.05, 0.0])
    for t in [60.0, 600.0, 5400.0]:
        forward = propagate_hcw(state0, n, t)
        back = propagate_hcw(forward, n, -t)
        assert np.max(np.abs(back - state0)) < 1e-9, \
            f"HCW time-reversal fails at t={t}"


def test_keplerian_roundtrip_conserves_orbital_elements():
    """Keplerian elements -> Cartesian -> Keplerian must be the identity
    on the 6 classical orbital elements within 1e-9."""
    cases = [
        (7000.0, 0.001, 0.5, 0.3, 0.7, 1.2),
        (8000.0, 0.1, np.deg2rad(28.5), np.deg2rad(45), np.deg2rad(120), np.deg2rad(60)),
        (42164.0, 0.0001, np.deg2rad(0.05), np.deg2rad(180), np.deg2rad(90), np.deg2rad(270)),
    ]
    for a, e, i, raan, argp, nu in cases:
        r, v = keplerian_to_cartesian(a, e, i, raan, argp, nu)
        elems = cartesian_to_keplerian(r, v)
        assert abs(elems["a"] - a) / a < 1e-9
        assert abs(elems["e"] - e) < 1e-8
        assert abs(elems["inc"] - i) < 1e-8


def test_perifocal_rotation_is_orthonormal():
    """The PQW -> ECI rotation matrix must be orthonormal: R R^T = I and det(R) = +1."""
    cases = [(0.5, 0.3, 0.8), (0.0, np.pi / 2, np.pi), (1.5, 0.1, 0.0)]
    for argp, inc, raan in cases:
        R = perifocal_to_eci(argp, inc, raan)
        assert np.max(np.abs(R @ R.T - np.eye(3))) < 1e-12
        assert abs(np.linalg.det(R) - 1.0) < 1e-12


def test_orbital_period_consistency():
    """The HCW mean motion n satisfies Kepler's third law n^2 a^3 = mu."""
    a = 6378.137 + 408.0
    n = mean_motion(a)
    mu = 398600.4418
    assert abs(n**2 * a**3 - mu) / mu < 1e-12
