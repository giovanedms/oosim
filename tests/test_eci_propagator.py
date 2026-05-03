"""Tests for oosim.proxops.eci_propagator.

Five test cases:
    1. Circular orbit closes after one period (1 m position tolerance).
    2. Zero-time propagation returns identical state.
    3. ISS-like orbit RAAN drifts ~-5°/day under J2 (±0.5° tolerance).
    4. propagate_orbit returns shape (N, 6) for N timestamps.
    5. Specific energy is conserved within 1e-9 along one elliptic orbit.
"""
import numpy as np
import pytest

from oosim.proxops.eci_propagator import (
    MU_EARTH,
    R_EARTH,
    propagate_kepler,
    propagate_kepler_j2,
    propagate_orbit,
)
from oosim.utils.frames_extra import keplerian_to_cartesian, cartesian_to_keplerian


# ─────────────────────────── helper ──────────────────────────────────────────

def _circular_state(radius_km: float, mu: float = MU_EARTH) -> np.ndarray:
    """Simple circular orbit in the equatorial plane (x-axis start)."""
    v_circ = np.sqrt(mu / radius_km)
    return np.array([radius_km, 0.0, 0.0, 0.0, v_circ, 0.0])


def _orbital_period(a_km: float, mu: float = MU_EARTH) -> float:
    return 2.0 * np.pi * np.sqrt(a_km**3 / mu)


# ─────────────────────────── tests ───────────────────────────────────────────

def test_propagate_kepler_circular_orbit_returns_to_start():
    """After exactly one orbital period a circular orbit must close.

    Tolerance: 1 m = 0.001 km in position norm.
    """
    a = 7000.0  # km
    state0 = _circular_state(a)
    T = _orbital_period(a)

    state1 = propagate_kepler(state0, T)

    dr = np.linalg.norm(state1[:3] - state0[:3])
    assert dr < 0.001, f"Position error after 1 period: {dr*1e3:.3f} m (tolerance 1 m)"


def test_propagate_kepler_zero_time_identity():
    """t=0 must return a state numerically identical to the input."""
    state0 = _circular_state(8000.0)
    state1 = propagate_kepler(state0, 0.0)
    np.testing.assert_array_equal(state0, state1)


def test_propagate_kepler_j2_iss_raan_drift():
    """ISS-like orbit RAAN must drift ~-5° per day under J2.

    Setup: a = 6786 km (≈ 408 km altitude), e ≈ 0, i = 51.6°.
    Expected RAAN drift: ≈ -5.0 °/day (Montenbruck & Gill Table 3.1).
    Tolerance: ±0.5°.
    """
    a_iss = R_EARTH + 408.0   # km
    i_iss = np.deg2rad(51.6)
    r0, v0 = keplerian_to_cartesian(
        a=a_iss, e=1e-4, inc=i_iss,
        raan=0.0, argp=0.0, true_anom=0.0,
    )
    state0 = np.concatenate([r0, v0])

    one_day = 86400.0  # s
    state1 = propagate_kepler_j2(state0, one_day)

    elems0 = cartesian_to_keplerian(state0[:3], state0[3:])
    elems1 = cartesian_to_keplerian(state1[:3], state1[3:])

    raan_drift_deg = np.rad2deg(elems1["raan"] - elems0["raan"])

    # Wrap to (-180, 180) to handle 2π rollover
    raan_drift_deg = (raan_drift_deg + 180.0) % 360.0 - 180.0

    assert abs(raan_drift_deg - (-5.0)) < 0.5, (
        f"RAAN drift {raan_drift_deg:.3f}°/day, expected -5.0 ± 0.5°"
    )


def test_propagate_orbit_array_shape():
    """propagate_orbit must return shape (N, 6) for N timestamps."""
    state0 = _circular_state(7000.0)
    N = 100
    t_array = np.linspace(0.0, _orbital_period(7000.0), N)

    result = propagate_orbit(state0, t_array, include_j2=True)

    assert result.shape == (N, 6), f"Expected ({N}, 6), got {result.shape}"


def test_propagate_kepler_energy_conservation():
    """Specific orbital energy E = v²/2 − μ/r must be constant within 1e-9.

    Uses elliptic orbit (a=8000 km, e=0.1) sampled at 50 points over 1 period.
    No J2 so only Kepler propagator is exercised.
    """
    a, e = 8000.0, 0.1
    mu = MU_EARTH
    r0, v0 = keplerian_to_cartesian(
        a=a, e=e, inc=np.deg2rad(28.5),
        raan=0.0, argp=0.0, true_anom=0.0,
    )
    state0 = np.concatenate([r0, v0])
    T = _orbital_period(a, mu)

    # Reference energy
    E0 = 0.5 * np.dot(v0, v0) - mu / np.linalg.norm(r0)

    t_array = np.linspace(0.0, T, 50)
    states = propagate_orbit(state0, t_array, include_j2=False)

    for k, state in enumerate(states):
        r_k = state[:3]
        v_k = state[3:]
        Ek = 0.5 * np.dot(v_k, v_k) - mu / np.linalg.norm(r_k)
        rel_err = abs(Ek - E0) / abs(E0)
        assert rel_err < 1e-9, (
            f"Energy not conserved at step {k}: rel_err = {rel_err:.2e}"
        )
