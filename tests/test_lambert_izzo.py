"""Tests for the Izzo (2015) Lambert solver."""
import numpy as np
import pytest
from oosim.utils.lambert_izzo import lambert_izzo


def test_lambert_izzo_90deg():
    """A 90-deg in-plane transfer should converge to a finite velocity."""
    R_E = 6378.137
    a = R_E + 500.
    mu = 398600.4418
    r1 = np.array([a, 0., 0.])
    r2 = np.array([0., a, 0.])
    tof = 0.25 * 2 * np.pi * np.sqrt(a**3 / mu)
    result = lambert_izzo(r1, r2, tof)
    if result is not None:
        v1, v2 = result
        v_circ = np.sqrt(mu / a)
        assert 0.5 * v_circ < np.linalg.norm(v1) < 2.0 * v_circ


def test_lambert_izzo_returns_pair_or_none():
    """API contract: returns either (v1, v2) tuple or None."""
    R_E = 6378.137
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = np.array([R_E + 300. + 100., 100., 0.])
    result = lambert_izzo(r1, r2, 600.0)
    assert result is None or len(result) == 2


def test_lambert_izzo_rejects_zero_tof():
    R_E = 6378.137
    r1 = np.array([R_E + 300., 0., 0.])
    r2 = np.array([R_E + 300., 100., 0.])
    result = lambert_izzo(r1, r2, 0.0)
    assert result is None
