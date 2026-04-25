"""Tests for additional coordinate-frame transforms."""
import numpy as np
from oosim.utils.frames_extra import (
    eci_to_ecef, perifocal_to_eci, keplerian_to_cartesian, cartesian_to_keplerian,
)


def test_keplerian_roundtrip():
    """Convert classical elements -> cartesian -> back; should match within 1e-6."""
    a, e, inc, raan, argp, nu = 7000.0, 0.01, 0.5, 0.3, 0.7, 1.2
    r, v = keplerian_to_cartesian(a, e, inc, raan, argp, nu)
    elems = cartesian_to_keplerian(r, v)
    assert abs(elems["a"] - a) < 1e-6
    assert abs(elems["e"] - e) < 1e-9
    assert abs(elems["inc"] - inc) < 1e-9
    assert abs(elems["raan"] - raan) < 1e-9
    assert abs(elems["argp"] - argp) < 1e-9
    assert abs(elems["true_anom"] - nu) < 1e-9


def test_eci_to_ecef_zero_gmst_identity():
    r = np.array([1000., 2000., 3000.])
    r_ecef = eci_to_ecef(r, 0.0)
    assert np.allclose(r_ecef, r)


def test_perifocal_to_eci_orthonormal():
    R = perifocal_to_eci(0.5, 0.3, 0.8)
    # Rotation matrix must be orthonormal: R R^T = I, det(R) = 1
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-10)
    assert abs(np.linalg.det(R) - 1.0) < 1e-10
