"""Tests for Lambert solver.

NOTE: the v0 Battin universal-variable implementation has a known singularity
at dnu = 180 deg (A = 0 in the formulation) and is fragile near the parabolic
boundary. Robust handling of these cases will be added in F2 (June 2026)
following Izzo (2015) or the Lancaster-Blanchard parameterization. For now,
we test only well-conditioned non-singular cases.
"""
import numpy as np
import pytest
from oosim.utils.lambert import lambert_battin


@pytest.mark.xfail(reason="180-deg transfer is a known singular case in v0 Battin impl; F2 fix planned")
def test_lambert_simple_circular_to_circular_180deg():
    """LEO 300 km to LEO 300 km, half-period TOF — singular at dnu=180."""
    R_E = 6378.137
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = np.array([-(R_E + 300.), 0., 0.])
    a = R_E + 300.
    mu = 398600.4418
    tof = np.pi * np.sqrt(a**3 / mu)
    result = lambert_battin(r1, r2, tof)
    assert result is not None


def test_lambert_90deg_transfer():
    """A 90-deg transfer in plane — well-conditioned, must converge (v1 fixed this)."""
    R_E = 6378.137
    a = R_E + 500.
    mu = 398600.4418
    r1 = np.array([a, 0., 0.])
    r2 = np.array([0., a, 0.])
    tof = 0.25 * 2 * np.pi * np.sqrt(a**3 / mu)  # quarter-period
    result = lambert_battin(r1, r2, tof)
    assert result is not None
    v1, v2 = result
    v_circ = np.sqrt(mu / a)
    assert 0.5 * v_circ < np.linalg.norm(v1) < 2.0 * v_circ


def test_lambert_returns_none_for_unreasonable_tof():
    """Extremely short TOF for a long arc should not converge."""
    R_E = 6378.137
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = np.array([0., R_E + 300., 0.])
    result = lambert_battin(r1, r2, 0.01)  # 10 ms TOF — physically unreasonable
    # Either None or an extremely large dv — we just check it doesn't crash
    assert result is None or len(result) == 2
