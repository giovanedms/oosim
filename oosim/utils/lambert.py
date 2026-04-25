"""Lambert problem solver: minimum-energy two-impulse transfer between
prescribed initial and final position vectors in a Keplerian gravity field.

Implementation: Battin's universal-variable iteration (per Vallado 2022, Ch. 7).
For multi-revolution branches, see Izzo (2015) which is not implemented here.

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed., Microcosm.
    Battin, R. H. (1999). An Introduction to the Mathematics and Methods of
        Astrodynamics, Revised Edition. AIAA Education Series.
"""
import numpy as np
from scipy.optimize import brentq

MU_EARTH = 398600.4418  # km^3/s^2


def lambert_battin(r1: np.ndarray, r2: np.ndarray, tof: float,
                   mu: float = MU_EARTH, prograde: bool = True,
                   max_iter: int = 50, tol: float = 1e-9
                   ) -> tuple[np.ndarray, np.ndarray] | None:
    """Solve Lambert's problem: find v1, v2 such that orbit through r1, r2 with TOF.

    Args:
        r1: 3-vector initial position [km].
        r2: 3-vector final position [km].
        tof: time of flight [s].
        mu: gravitational parameter [km^3/s^2].
        prograde: True for posigrade transfer (typical), False for retrograde.

    Returns:
        (v1, v2) departure and arrival velocity vectors [km/s], or None if
        no solution converged.
    """
    r1n = float(np.linalg.norm(r1))
    r2n = float(np.linalg.norm(r2))
    cos_dnu = float(np.dot(r1, r2)) / (r1n * r2n)
    cross = np.cross(r1, r2)

    if prograde:
        dnu = np.arccos(np.clip(cos_dnu, -1.0, 1.0))
        if cross[2] < 0.0:
            dnu = 2 * np.pi - dnu
    else:
        dnu = np.arccos(np.clip(cos_dnu, -1.0, 1.0))
        if cross[2] > 0.0:
            dnu = 2 * np.pi - dnu

    A = np.sin(dnu) * np.sqrt(r1n * r2n / (1.0 - cos_dnu))
    if A == 0.0:
        return None

    # Universal-variable iteration on z (Stumpff functions C(z), S(z))
    def C(z):
        if abs(z) < 1e-6:
            return 0.5 - z / 24.0
        if z > 0:
            sz = np.sqrt(z)
            return (1 - np.cos(sz)) / z
        sz = np.sqrt(-z)
        return (np.cosh(sz) - 1) / (-z)

    def S(z):
        if abs(z) < 1e-6:
            return 1.0 / 6.0 - z / 120.0
        if z > 0:
            sz = np.sqrt(z)
            return (sz - np.sin(sz)) / sz**3
        sz = np.sqrt(-z)
        return (np.sinh(sz) - sz) / sz**3

    def y(z):
        cz = C(z); sz_val = S(z)
        if cz <= 0:
            return None
        return r1n + r2n + A * (z * sz_val - 1.0) / np.sqrt(cz)

    def F(z):
        yz = y(z)
        if yz is None or yz < 0:
            return None
        cz = C(z)
        return (yz / cz) ** 1.5 * S(z) + A * np.sqrt(yz) - np.sqrt(mu) * tof

    # Bracket the root: typical range z in [-50, 4*pi^2]
    try:
        z_root = brentq(lambda z: F(z) or 0.0, -50.0, 4 * np.pi**2,
                        xtol=tol, maxiter=max_iter)
    except (ValueError, RuntimeError):
        return None

    yz = y(z_root)
    if yz is None:
        return None
    f = 1.0 - yz / r1n
    g = A * np.sqrt(yz / mu)
    g_dot = 1.0 - yz / r2n

    v1 = (r2 - f * r1) / g
    v2 = (g_dot * r2 - r1) / g
    return v1, v2
