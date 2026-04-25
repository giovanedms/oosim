"""J2 oblateness secular perturbation on Keplerian elements.

Closed-form secular rates for Right Ascension of the Ascending Node (RAAN),
argument of perigee, and mean anomaly under J2.

References:
    Montenbruck, O. & Gill, E. (2000). Satellite Orbits. Springer.
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed. Microcosm.
"""
import numpy as np

J2_EARTH = 1.08262668e-3
R_EARTH = 6378.137  # km
MU_EARTH = 398600.4418  # km^3/s^2


def secular_rates_j2(a: float, e: float, i: float,
                     mu: float = MU_EARTH,
                     j2: float = J2_EARTH,
                     r_body: float = R_EARTH) -> tuple[float, float, float]:
    """Compute J2 secular rates (Omega_dot, omega_dot, M_dot) in rad/s.

    Args:
        a: semi-major axis [km].
        e: eccentricity.
        i: inclination [rad].

    Returns:
        (raan_dot, argp_dot, mean_anomaly_dot) all in rad/s.
    """
    n = np.sqrt(mu / a**3)
    p = a * (1 - e**2)
    factor = -1.5 * n * j2 * (r_body / p) ** 2

    raan_dot = factor * np.cos(i)
    argp_dot = factor * (2.5 * np.sin(i) ** 2 - 2.0)
    mean_anomaly_dot = n + factor * np.sqrt(1 - e**2) * (1.5 * np.sin(i) ** 2 - 1.0)

    return float(raan_dot), float(argp_dot), float(mean_anomaly_dot)


def nodal_regression_iss(altitude_km: float = 408.0, inclination_deg: float = 51.6) -> float:
    """Convenience: RAAN drift rate for ISS-like orbit, in deg/day."""
    a = R_EARTH + altitude_km
    raan_dot, _, _ = secular_rates_j2(a, 0.0, np.deg2rad(inclination_deg))
    return float(np.rad2deg(raan_dot) * 86400.0)
