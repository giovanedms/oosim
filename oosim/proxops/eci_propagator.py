"""ECI propagator: Kepler universal-variable (Vallado Alg.8) + J2 secular drift.

Implements:
    propagate_kepler       — pure Kepler propagation via universal variable
    propagate_kepler_j2    — Kepler + J2 secular drift on RAAN, argp, M
    propagate_orbit        — high-level wrapper returning (N, 6) array

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics and Applications,
        5th ed. Microcosm Press. Algorithm 8 (universal-variable Kepler).
    Montenbruck, O. & Gill, E. (2000). Satellite Orbits. Springer.
"""
import numpy as np

from oosim.utils.frames_extra import keplerian_to_cartesian, cartesian_to_keplerian
from oosim.phasing.j2 import secular_rates_j2

# ──────────────────────────────── Constants ───────────────────────────────────
MU_EARTH: float = 398600.4418   # km³/s²
R_EARTH: float = 6378.137       # km
J2_EARTH: float = 1.08262668e-3

# ──────────────────────────── Stumpff functions ───────────────────────────────

def _stumpff_C(psi: float) -> float:
    """Stumpff function C(ψ) (also written c₂)."""
    if psi > 1e-6:
        return (1.0 - np.cos(np.sqrt(psi))) / psi
    if psi < -1e-6:
        sq = np.sqrt(-psi)
        return (np.cosh(sq) - 1.0) / (-psi)
    # Taylor series around psi = 0
    return 0.5 - psi / 24.0 + psi**2 / 720.0


def _stumpff_S(psi: float) -> float:
    """Stumpff function S(ψ) (also written c₃)."""
    if psi > 1e-6:
        sq = np.sqrt(psi)
        return (sq - np.sin(sq)) / (psi * sq)
    if psi < -1e-6:
        sq = np.sqrt(-psi)
        return (np.sinh(sq) - sq) / ((-psi) * sq)
    # Taylor series around psi = 0
    return 1.0 / 6.0 - psi / 120.0 + psi**2 / 5040.0


# ──────────────────── Universal-variable Kepler propagation ───────────────────

def propagate_kepler(
    state_eci: np.ndarray,
    t_seconds: float,
    mu: float = MU_EARTH,
) -> np.ndarray:
    """Propagate a 6-vector ECI state under two-body (Kepler) dynamics.

    Uses the universal-variable formulation (Vallado Algorithm 8) which handles
    circular, elliptic, parabolic and hyperbolic orbits uniformly.

    Args:
        state_eci: [rx, ry, rz, vx, vy, vz] in km and km/s.
        t_seconds: propagation interval [s].  May be negative.
        mu:        gravitational parameter [km³/s²].

    Returns:
        New 6-vector [rx, ry, rz, vx, vy, vz] in km and km/s.
    """
    r0 = np.asarray(state_eci[:3], dtype=float)
    v0 = np.asarray(state_eci[3:], dtype=float)

    if t_seconds == 0.0:
        return np.array(state_eci, dtype=float)

    r0_norm = float(np.linalg.norm(r0))
    v0_norm = float(np.linalg.norm(v0))
    alpha = 2.0 / r0_norm - v0_norm**2 / mu   # 1/a  (positive for ellipse)

    # Initial guess for universal variable χ (Vallado Eq. 2-38)
    if alpha > 1e-6:  # elliptic
        chi0 = np.sqrt(mu) * t_seconds * alpha
    elif abs(alpha) < 1e-6:  # parabolic
        h = np.cross(r0, v0)
        p = np.linalg.norm(h)**2 / mu
        s = 0.5 * np.arctan(1.0 / (3.0 * np.sqrt(mu / p**3) * t_seconds))
        w = np.arctan(np.cbrt(np.tan(s)))
        chi0 = np.sqrt(2.0 * p) / np.tan(2.0 * w)
    else:  # hyperbolic
        a = 1.0 / alpha
        chi0 = (np.sign(t_seconds)
                * np.sqrt(-a)
                * np.log((-2.0 * mu * alpha * t_seconds)
                         / (np.dot(r0, v0)
                            + np.sign(t_seconds) * np.sqrt(-mu * a)
                            * (1.0 - r0_norm * alpha))))

    # Newton-Raphson iteration
    chi = float(chi0)
    sqrt_mu = np.sqrt(mu)
    r_dot_v0 = float(np.dot(r0, v0))

    for _ in range(50):
        psi = chi**2 * alpha
        C = _stumpff_C(psi)
        S = _stumpff_S(psi)

        r_chi = (chi**2 * C
                 + (r_dot_v0 / sqrt_mu) * chi * (1.0 - psi * S)
                 + r0_norm * (1.0 - psi * C))

        dt_chi = (chi**3 * S
                  + (r_dot_v0 / sqrt_mu) * chi**2 * C
                  + r0_norm * chi * (1.0 - psi * S)) / sqrt_mu

        delta = (t_seconds - dt_chi) / (r_chi / sqrt_mu)
        chi += delta
        if abs(delta) < 1e-12:
            break

    # Lagrange coefficients (Vallado Eq. 2-44 to 2-47)
    psi = chi**2 * alpha
    C = _stumpff_C(psi)
    S = _stumpff_S(psi)

    f = 1.0 - chi**2 * C / r0_norm
    g = t_seconds - chi**3 * S / sqrt_mu

    r1 = f * r0 + g * v0
    r1_norm = float(np.linalg.norm(r1))

    f_dot = sqrt_mu * chi * (psi * S - 1.0) / (r1_norm * r0_norm)
    g_dot = 1.0 - chi**2 * C / r1_norm

    v1 = f_dot * r0 + g_dot * v0

    return np.concatenate([r1, v1])


# ─────────────────────── Kepler + J2 secular propagation ─────────────────────

def propagate_kepler_j2(
    state_eci: np.ndarray,
    t_seconds: float,
    mu: float = MU_EARTH,
    j2: float = J2_EARTH,
    r_body: float = R_EARTH,
) -> np.ndarray:
    """Propagate ECI state under Kepler + J2 secular drift.

    Algorithm:
        1. Convert Cartesian → Keplerian elements.
        2. Compute J2 secular rates (raan_dot, argp_dot, M_dot_extra).
        3. Apply secular drifts to RAAN, argp, mean anomaly over Δt.
        4. Convert back to Cartesian.

    The mean-motion contribution to M is folded into secular_rates_j2
    (mean_anomaly_dot already includes n), so the new mean anomaly is:
        M_new = M0 + mean_anomaly_dot * t

    Args:
        state_eci: [rx, ry, rz, vx, vy, vz] in km and km/s.
        t_seconds: propagation interval [s].
        mu:        gravitational parameter [km³/s²].
        j2:        J2 coefficient (dimensionless).
        r_body:    equatorial radius [km].

    Returns:
        New 6-vector in km and km/s.
    """
    r0 = np.asarray(state_eci[:3], dtype=float)
    v0 = np.asarray(state_eci[3:], dtype=float)

    if t_seconds == 0.0:
        return np.array(state_eci, dtype=float)

    # Step 1: Cartesian → Keplerian
    elems = cartesian_to_keplerian(r0, v0, mu=mu)
    a = elems["a"]
    e = elems["e"]
    inc = elems["inc"]
    raan = elems["raan"]
    argp = elems["argp"]
    nu0 = elems["true_anom"]

    # Step 2: Convert true anomaly → eccentric → mean anomaly
    # E = 2 * arctan(sqrt((1-e)/(1+e)) * tan(nu/2))
    E0 = 2.0 * np.arctan2(
        np.sqrt(1.0 - e) * np.sin(nu0 / 2.0),
        np.sqrt(1.0 + e) * np.cos(nu0 / 2.0),
    )
    M0 = E0 - e * np.sin(E0)

    # Step 3: J2 secular rates — mean_anomaly_dot already includes n
    raan_dot, argp_dot, M_dot = secular_rates_j2(a, e, inc, mu=mu, j2=j2, r_body=r_body)

    raan_new = raan + raan_dot * t_seconds
    argp_new = argp + argp_dot * t_seconds
    M_new = M0 + M_dot * t_seconds

    # Step 4: Solve Kepler's equation  M = E - e*sin(E)  (Newton-Raphson)
    E = M_new  # initial guess
    for _ in range(50):
        dE = (M_new - E + e * np.sin(E)) / (1.0 - e * np.cos(E))
        E += dE
        if abs(dE) < 1e-13:
            break

    # Eccentric → true anomaly
    nu_new = 2.0 * np.arctan2(
        np.sqrt(1.0 + e) * np.sin(E / 2.0),
        np.sqrt(1.0 - e) * np.cos(E / 2.0),
    )

    # Step 5: Keplerian → Cartesian
    r1, v1 = keplerian_to_cartesian(a, e, inc, raan_new, argp_new, nu_new, mu=mu)
    return np.concatenate([r1, v1])


# ──────────────────────────── High-level wrapper ──────────────────────────────

def propagate_orbit(
    state_eci_initial: np.ndarray,
    t_array: np.ndarray,
    mu: float = MU_EARTH,
    include_j2: bool = True,
) -> np.ndarray:
    """Propagate an initial ECI state over a time array.

    Args:
        state_eci_initial: [rx, ry, rz, vx, vy, vz] at t=0, km and km/s.
        t_array:           1-D array of times [s] relative to t=0.
        mu:                gravitational parameter [km³/s²].
        include_j2:        if True, use J2 secular drift; else pure Kepler.

    Returns:
        Array of shape (N, 6) with ECI state at each timestamp.
    """
    t_array = np.asarray(t_array, dtype=float)
    propagator = propagate_kepler_j2 if include_j2 else propagate_kepler

    states = np.empty((len(t_array), 6), dtype=float)
    for k, t in enumerate(t_array):
        states[k] = propagator(state_eci_initial, float(t), mu=mu)

    return states
