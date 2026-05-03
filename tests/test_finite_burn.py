"""Tests for oosim.phasing.finite_burn (Vallado Alg. 6-79)."""
import numpy as np
import pytest

from oosim.phasing.finite_burn import (
    burn_duration,
    effective_thrust_direction,
    finite_burn_corrected_dv,
    finite_burn_loss_factor,
    hohmann_with_finite_burns,
)


# ---------------------------------------------------------------------------
# Test 1 — zero Δv → loss factor = 1 (no loss)
# ---------------------------------------------------------------------------
def test_loss_factor_zero_dv_returns_unity():
    """With zero impulsive Δv the loss factor must equal 1 exactly."""
    factor = finite_burn_loss_factor(
        thrust_acceleration=0.0,
        dv_impulsive=0.0,
        v_circ=7.66,  # km/s (typical ISS)
    )
    assert factor == pytest.approx(1.0, rel=1e-12)


# ---------------------------------------------------------------------------
# Test 2 — typical ISS burn: small loss, factor very close to 1
# ---------------------------------------------------------------------------
def test_loss_factor_typical_iss_burn_small():
    """For Δv=50 m/s at ISS altitude (v_circ≈7.66 km/s) the loss is tiny.

    Expected: loss_factor ≈ 1 − (1/24)*(0.05/7.66)² ≈ 0.999986
    """
    dv_m_s = 50.0
    v_circ_km_s = 7.66
    factor = finite_burn_loss_factor(
        thrust_acceleration=0.0,  # not used in simplified model
        dv_impulsive=dv_m_s,
        v_circ=v_circ_km_s,
    )
    ratio = (dv_m_s / 1000.0) / v_circ_km_s
    expected = 1.0 - (1.0 / 24.0) * ratio**2
    assert factor == pytest.approx(expected, rel=1e-9)
    # Sanity: very close to 1
    assert 0.9999 < factor < 1.0


# ---------------------------------------------------------------------------
# Test 3 — corrected Δv must exceed the impulsive estimate
# ---------------------------------------------------------------------------
def test_corrected_dv_greater_than_impulsive():
    """The finite-burn corrected Δv must always be ≥ the impulsive Δv."""
    dv_imp = 100.0       # m/s
    v_circ = 7.66        # km/s
    thrust_accel = 0.05  # m/s² (400 N / 8000 kg)
    dv_corr = finite_burn_corrected_dv(dv_imp, thrust_accel, v_circ)
    assert dv_corr > dv_imp, (
        f"Corrected Δv ({dv_corr:.6f} m/s) should exceed impulsive ({dv_imp} m/s)"
    )


# ---------------------------------------------------------------------------
# Test 4 — Soyuz-class burn duration
# ---------------------------------------------------------------------------
def test_burn_duration_typical_soyuz():
    """Soyuz KTDU-80: 2950 N, 7150 kg, Δv=50 m/s → t_burn ≈ 121.2 s."""
    dv = 50.0      # m/s
    thrust = 2950.0  # N
    mass = 7150.0    # kg
    t = burn_duration(dv, thrust, mass)
    # t = dv * mass / thrust = 50 * 7150 / 2950 ≈ 121.186 s
    expected = dv * mass / thrust
    assert t == pytest.approx(expected, rel=1e-9)
    assert 120.0 < t < 123.0, f"Expected ~121 s, got {t:.2f} s"


# ---------------------------------------------------------------------------
# Additional smoke tests (not required by spec but guard regressions)
# ---------------------------------------------------------------------------
def test_effective_thrust_direction_zero_omega():
    """For ω=0, effective direction equals initial direction."""
    d_init = np.array([1.0, 0.0, 0.0])
    d_eff = effective_thrust_direction(d_init, omega_chaser_rad_s=0.0, t_burn_s=60.0)
    np.testing.assert_allclose(d_eff, d_init)


def test_hohmann_with_finite_burns_corrected_greater():
    """Finite-burn corrected Δv must exceed the impulsive values for a typical LEO→ISS transfer."""
    from oosim.phasing.hohmann import hohmann_dv

    r1, r2 = 6578.0, 6778.0  # km
    dv1_imp, dv2_imp, _ = hohmann_dv(r1, r2)
    dv1_corr, dv2_corr, t1, t2 = hohmann_with_finite_burns(r1, r2)
    # corrected values in m/s vs impulsive in km/s
    assert dv1_corr > dv1_imp * 1000.0
    assert dv2_corr > dv2_imp * 1000.0
    assert t1 > 0.0
    assert t2 > 0.0
