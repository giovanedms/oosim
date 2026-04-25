"""Hohmann transfer between coplanar circular orbits.

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics and Applications, 5th ed.
    Curtis, H. D. (2020). Orbital Mechanics for Engineering Students, 4th ed.
"""
import numpy as np

MU_EARTH = 398600.4418  # km^3/s^2


def hohmann_dv(r1: float, r2: float, mu: float = MU_EARTH) -> tuple[float, float, float]:
    """Compute the two-impulse Hohmann transfer delta-v between coplanar circular orbits.

    Args:
        r1: initial orbit radius [km].
        r2: final orbit radius [km].
        mu: gravitational parameter [km^3/s^2].

    Returns:
        (dv1, dv2, dv_total) in km/s.
    """
    a_t = 0.5 * (r1 + r2)
    v1 = np.sqrt(mu / r1)
    v2 = np.sqrt(mu / r2)
    v_t1 = np.sqrt(mu * (2.0 / r1 - 1.0 / a_t))
    v_t2 = np.sqrt(mu * (2.0 / r2 - 1.0 / a_t))
    dv1 = abs(v_t1 - v1)
    dv2 = abs(v2 - v_t2)
    return dv1, dv2, dv1 + dv2


def hohmann_time_of_flight(r1: float, r2: float, mu: float = MU_EARTH) -> float:
    """Half-period of the transfer ellipse in seconds."""
    a_t = 0.5 * (r1 + r2)
    return float(np.pi * np.sqrt(a_t**3 / mu))
