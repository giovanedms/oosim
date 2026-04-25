"""Tests for J2 secular perturbation."""
import numpy as np
from oosim.phasing.j2 import secular_rates_j2, nodal_regression_iss


def test_iss_nodal_regression():
    """ISS at 408 km, 51.6 deg should regress ~5 deg/day westward.

    Reference: Vallado Ch.9, Wertz SMAD Ch.6.
    """
    deg_per_day = nodal_regression_iss(altitude_km=408.0, inclination_deg=51.6)
    # Negative because westward; magnitude ~4.9-5.0 deg/day for ISS
    assert -5.2 < deg_per_day < -4.7


def test_polar_orbit_no_raan_drift():
    """Pure polar orbit (i=90 deg) has cos(i)=0 -> no RAAN drift."""
    a = 6378.137 + 800.0
    raan_dot, _, _ = secular_rates_j2(a, 0.001, np.pi / 2)
    assert abs(raan_dot) < 1e-12


def test_critical_inclination():
    """At i ≈ 63.4349 deg, argument of perigee drift vanishes (5*sin^2 i = 4)."""
    a = 6378.137 + 700.0
    i_crit = np.arcsin(np.sqrt(4.0 / 5.0))
    _, argp_dot, _ = secular_rates_j2(a, 0.01, i_crit)
    assert abs(argp_dot) < 1e-12
