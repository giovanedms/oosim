"""Finite-burn correction for impulsive Hohmann transfers.

Implements Vallado Algorithm 6-79 (gravitational loss factor) and supporting
utilities for converting impulsive Δv estimates into realistic burn parameters.

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics and Applications,
    5th ed., Microcosm Press. Eq. 6-79 (gravitational loss during finite burn).
"""
import numpy as np

from oosim.phasing.hohmann import hohmann_dv

MU_EARTH = 398600.4418  # km^3/s^2
R_EARTH = 6378.137      # km


def finite_burn_loss_factor(
    thrust_acceleration: float,  # noqa: ARG001  (reserved for future hi-fidelity model)
    dv_impulsive: float,
    v_circ: float,
) -> float:
    """Gravitational loss factor for a finite-duration burn (Vallado Eq. 6-79).

    The impulsive Δv must be scaled by 1/loss_factor to account for gravity
    losses during the burn. For short burns (dv << v_circ) the factor is very
    close to 1.

    Args:
        thrust_acceleration: thrust-to-mass ratio [m/s²] (reserved for
            higher-fidelity extensions; the simplified Eq. 6-79 uses the
            ratio dv/v_circ only).
        dv_impulsive: impulsive Δv magnitude [m/s].
        v_circ: circular orbital speed at burn altitude [km/s].

    Returns:
        loss_factor (unitless, ~1 for short burns, <1 otherwise).
    """
    # Vallado Eq. 6-79: loss ≈ (1/24) * (Δv/v_circ)²
    # Both quantities must be in consistent units; convert dv to km/s.
    dv_km_s = dv_impulsive / 1000.0  # m/s → km/s
    ratio = dv_km_s / v_circ
    return float(1.0 - (1.0 / 24.0) * ratio**2)


def finite_burn_corrected_dv(
    dv_impulsive: float,
    thrust_acceleration_m_s2: float,
    v_circ_km_s: float,
) -> float:
    """Return the Δv the thruster must actually deliver for the desired orbit change.

    Because gravity acts against the vehicle during a finite burn, the required
    delivered Δv is larger than the impulsive estimate.

    Args:
        dv_impulsive: impulsive Δv [m/s].
        thrust_acceleration_m_s2: thrust / mass [m/s²].
        v_circ_km_s: circular speed at burn altitude [km/s].

    Returns:
        Corrected Δv [m/s] (always ≥ dv_impulsive).
    """
    factor = finite_burn_loss_factor(
        thrust_acceleration_m_s2, dv_impulsive, v_circ_km_s
    )
    # Guard against degenerate factor (should not happen for realistic orbits)
    if factor <= 0.0:
        raise ValueError(
            f"loss_factor={factor:.6f} ≤ 0 — burn duration exceeds orbital period."
        )
    return float(dv_impulsive / factor)


def burn_duration(dv_real_m_s: float, thrust_N: float, mass_kg: float) -> float:
    """Compute burn duration from rocket equation (constant-thrust approximation).

    Δm is ignored (constant mass assumption valid when Δv << exhaust velocity).
    For typical chemical thrusters and Δv < 200 m/s the error is < 1 %.

    Args:
        dv_real_m_s: actual Δv to be delivered [m/s].
        thrust_N: engine thrust [N].
        mass_kg: chaser mass [kg].

    Returns:
        Burn duration [s].
    """
    if thrust_N <= 0.0:
        raise ValueError("thrust_N must be positive.")
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive.")
    return float(dv_real_m_s * mass_kg / thrust_N)


def effective_thrust_direction(
    thrust_direction_initial: np.ndarray,
    omega_chaser_rad_s: float,
    t_burn_s: float,
) -> np.ndarray:
    """Average thrust direction over a finite burn when the chaser body-rotates.

    During a burn of duration t_burn the vehicle rotates by ω·t_burn rad.
    The time-averaged direction (sinc approximation) is:

        d_eff ≈ d_init · sinc(ω·t_burn / (2π))   [numpy sinc convention]

    which equals  d_init · sin(ω·t_burn/2) / (ω·t_burn/2)  for ω ≠ 0.
    Each component is scaled independently (attitude hold per axis).

    Args:
        thrust_direction_initial: unit vector of thrust at burn start [3-element].
        omega_chaser_rad_s: angular rate magnitude of the chaser [rad/s].
        t_burn_s: burn duration [s].

    Returns:
        Effective (time-averaged) thrust direction [same shape as input].
    """
    thrust_direction_initial = np.asarray(thrust_direction_initial, dtype=float)
    half_angle = omega_chaser_rad_s * t_burn_s / 2.0
    if abs(half_angle) < 1e-12:
        # ω ≈ 0 or t_burn ≈ 0: direction unchanged
        return thrust_direction_initial.copy()
    sinc_factor = np.sin(half_angle) / half_angle
    return thrust_direction_initial * sinc_factor


def hohmann_with_finite_burns(
    r1_km: float,
    r2_km: float,
    thrust_N: float = 400.0,
    mass_kg: float = 7000.0,
    mu: float = MU_EARTH,
) -> tuple[float, float, float, float]:
    """Hohmann transfer with finite-burn correction applied to both impulses.

    Wraps :func:`~oosim.phasing.hohmann.hohmann_dv` and applies Vallado's
    gravitational loss correction to each burn.

    Args:
        r1_km: initial circular orbit radius [km].
        r2_km: final circular orbit radius [km].
        thrust_N: engine thrust [N].
        mass_kg: chaser wet mass at first burn [kg].
        mu: gravitational parameter [km^3/s^2].

    Returns:
        (dv1_corrected [m/s], dv2_corrected [m/s],
         t_burn1_s [s], t_burn2_s [s])
    """
    dv1_km_s, dv2_km_s, _ = hohmann_dv(r1_km, r2_km, mu)

    # Convert to m/s for finite-burn functions
    dv1_m_s = dv1_km_s * 1000.0
    dv2_m_s = dv2_km_s * 1000.0

    # Circular speed at each burn altitude
    v1_km_s = float(np.sqrt(mu / r1_km))
    v2_km_s = float(np.sqrt(mu / r2_km))

    thrust_accel = thrust_N / mass_kg  # m/s² (constant-mass approximation)

    dv1_corr = finite_burn_corrected_dv(dv1_m_s, thrust_accel, v1_km_s)
    dv2_corr = finite_burn_corrected_dv(dv2_m_s, thrust_accel, v2_km_s)

    t1 = burn_duration(dv1_corr, thrust_N, mass_kg)
    t2 = burn_duration(dv2_corr, thrust_N, mass_kg)

    return dv1_corr, dv2_corr, t1, t2
