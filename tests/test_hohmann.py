"""Sanity tests for Hohmann module — validate against textbook examples."""
import numpy as np
from oosim.phasing.hohmann import hohmann_dv, hohmann_time_of_flight, MU_EARTH


def test_hohmann_300_to_400_km():
    """Standard ISS-altitude reboost case from Vallado Ch.6."""
    R_E = 6378.137
    r1 = R_E + 300.0
    r2 = R_E + 400.0
    dv1, dv2, dv_total = hohmann_dv(r1, r2)
    # Expected ~28 m/s for first burn (matches Vallado).
    assert 0.025 < dv1 < 0.030
    assert 0.025 < dv2 < 0.030
    assert 0.052 < dv_total < 0.058


def test_hohmann_geo():
    """LEO to GEO transfer."""
    R_E = 6378.137
    r1 = R_E + 200.0
    r2 = 42164.0
    dv1, dv2, dv_total = hohmann_dv(r1, r2)
    # Expected ~3.94 km/s total (matches Curtis Ex. 6.2).
    assert 3.85 < dv_total < 4.00


def test_hohmann_tof_positive():
    tof = hohmann_time_of_flight(7000.0, 7100.0)
    assert tof > 0
    assert tof < 1e4
