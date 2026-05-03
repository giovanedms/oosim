"""Tests for frames_dynamic.py — dynamic ECI <-> LVLH transforms.

Tests:
    1. ECI -> LVLH -> ECI roundtrip (exact inverse)
    2. Collocated chaser/target → zero relative state
    3. ISS-like circular orbit: |omega| matches theoretical sqrt(mu/r^3)
    4. HCW consistency: track_relative_along_orbit for small offset over half orbit
"""
import numpy as np
import pytest

from oosim.utils.frames_dynamic import (
    lvlh_angular_velocity_in_eci,
    eci_state_to_lvlh_relative,
    lvlh_relative_to_eci_state,
    track_relative_along_orbit,
    MU_EARTH,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _circular_orbit_state(r_km: float, inclination_deg: float = 0.0):
    """Return (r_eci, v_eci) for a circular orbit of given radius [km]."""
    v_circ = np.sqrt(MU_EARTH / r_km)
    inc = np.radians(inclination_deg)
    r_eci = np.array([r_km, 0.0, 0.0])
    v_eci = np.array([0.0, v_circ * np.cos(inc), v_circ * np.sin(inc)])
    return r_eci, v_eci


def _two_body_propagator(state6: np.ndarray, t: float) -> np.ndarray:
    """Simple Keplerian propagator via RK4 for small t; used in track test."""
    from scipy.integrate import solve_ivp

    def eom(t_, y):
        r = y[:3]
        v = y[3:]
        r_norm = np.linalg.norm(r)
        a = -MU_EARTH / r_norm**3 * r
        return np.concatenate([v, a])

    if t == 0.0:
        return state6.copy()

    sol = solve_ivp(
        eom,
        [0.0, t],
        state6,
        method="RK45",
        rtol=1e-10,
        atol=1e-12,
        dense_output=False,
    )
    return sol.y[:, -1]


# ---------------------------------------------------------------------------
# Test 1 — ECI -> LVLH -> ECI roundtrip
# ---------------------------------------------------------------------------

def test_eci_to_lvlh_to_eci_roundtrip():
    """Converting LVLH relative state back to ECI should reproduce original."""
    r_target, v_target = _circular_orbit_state(7000.0, inclination_deg=28.5)

    # Arbitrary chaser offset (1 km radial, 0.5 km along-track, 0.2 km normal)
    r_chaser = r_target + np.array([1.0, 0.5, 0.2])
    v_chaser = v_target + np.array([0.001, -0.002, 0.0005])

    # Forward: ECI -> LVLH
    rel_lvlh = eci_state_to_lvlh_relative(r_chaser, v_chaser, r_target, v_target)

    # Inverse: LVLH -> ECI
    r_chaser_rec, v_chaser_rec = lvlh_relative_to_eci_state(rel_lvlh, r_target, v_target)

    np.testing.assert_allclose(r_chaser_rec, r_chaser, atol=1e-10,
                                err_msg="Position roundtrip failed")
    np.testing.assert_allclose(v_chaser_rec, v_chaser, atol=1e-10,
                                err_msg="Velocity roundtrip failed")


# ---------------------------------------------------------------------------
# Test 2 — Collocated chaser → zero relative state
# ---------------------------------------------------------------------------

def test_collocated_chaser_returns_zero_relative():
    """Chaser and target at identical ECI state must give zero LVLH relative."""
    r_eci, v_eci = _circular_orbit_state(6786.0, inclination_deg=51.6)

    rel = eci_state_to_lvlh_relative(r_eci, v_eci, r_eci, v_eci)

    np.testing.assert_allclose(rel, np.zeros(6), atol=1e-12,
                                err_msg="Collocated chaser must yield zero relative state")


# ---------------------------------------------------------------------------
# Test 3 — ISS-like circular orbit: angular velocity magnitude
# ---------------------------------------------------------------------------

def test_lvlh_angular_velocity_iss_circular():
    """For ISS-like circular orbit, |omega| must match sqrt(mu/r^3).

    ISS: r ≈ 6786 km (altitude ~408 km above equatorial radius 6378 km).
    Theoretical: omega_theory = sqrt(MU_EARTH / r^3) ≈ 1.1306 mrad/s.
    """
    r_km = 6786.0
    r_eci, v_eci = _circular_orbit_state(r_km)

    omega_theory = np.sqrt(MU_EARTH / r_km**3)  # [rad/s]

    omega_vec = lvlh_angular_velocity_in_eci(r_eci, v_eci)
    omega_mag = np.linalg.norm(omega_vec)

    # Tolerance: 1e-6 rad/s (theoretical circular approximation is exact here)
    assert abs(omega_mag - omega_theory) < 1e-9, (
        f"|omega| = {omega_mag:.6e} rad/s, expected {omega_theory:.6e} rad/s"
    )

    # Direction: omega must be in H-bar direction (orbit normal = ECI z for
    # equatorial orbit), i.e., parallel to r x v
    h_hat = np.cross(r_eci, v_eci)
    h_hat /= np.linalg.norm(h_hat)
    omega_hat = omega_vec / omega_mag
    dot = abs(np.dot(omega_hat, h_hat))
    assert dot > 1 - 1e-12, f"omega not aligned with orbit normal: dot={dot}"


# ---------------------------------------------------------------------------
# Test 4 — HCW consistency for small offset over half orbit
# ---------------------------------------------------------------------------

def test_track_relative_constant_offset():
    """Relative state from track_relative_along_orbit must be HCW-consistent.

    Setup:
        Target on circular orbit (r = 7000 km, equatorial).
        Chaser started with pure V-bar offset of 0.5 km (along-track) and
        zero relative velocity. Over time, HCW predicts the motion stays
        bounded (periodic for zero radial offset initial condition).

    Assertions:
        - Relative state magnitude stays bounded (< 2 km) over half orbit.
        - Relative position norm > 0.01 km for nonzero initial offset
          (chaser did not collapse to target).
        - Output shape is (N, 6).
    """
    r_km = 7000.0
    r_target, v_target = _circular_orbit_state(r_km)
    target_eci = np.concatenate([r_target, v_target])

    # Chaser: same orbit but 0.5 km along-track behind.
    # Recover chaser ECI by inverting a pure y-LVLH offset.
    offset_lvlh = np.array([0.0, 0.5, 0.0, 0.0, 0.0, 0.0])
    r_chaser, v_chaser = lvlh_relative_to_eci_state(offset_lvlh, r_target, v_target)
    chaser_eci = np.concatenate([r_chaser, v_chaser])

    # Half orbit period
    T_orbit = 2 * np.pi * np.sqrt(r_km**3 / MU_EARTH)  # [s]
    t_array = np.linspace(0, T_orbit / 2, 50)

    rel_states = track_relative_along_orbit(
        chaser_eci, target_eci, t_array, _two_body_propagator
    )

    # Shape check
    assert rel_states.shape == (50, 6), f"Expected (50,6), got {rel_states.shape}"

    # Boundedness: LVLH relative position norm < 2 km (HCW drift-free for y-only offset)
    pos_norms = np.linalg.norm(rel_states[:, :3], axis=1)
    assert np.all(pos_norms < 2.0), (
        f"Relative orbit exceeded bound: max={pos_norms.max():.3f} km"
    )

    # Non-collapse: chaser should not merge with target
    assert np.all(pos_norms > 0.01), (
        f"Relative orbit collapsed: min={pos_norms.min():.6f} km"
    )
