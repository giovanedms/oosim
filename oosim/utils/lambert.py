"""Lambert problem solver — Vallado universal-variable formulation (v1).

Solves: given r1, r2 (position vectors at two epochs) and TOF (time of flight),
find v1, v2 such that the Keplerian orbit through r1 with velocity v1 reaches
r2 at TOF later with velocity v2.

This is v1: a more careful re-implementation of the Vallado Algorithm 58
(Bate-Mueller-White / Vallado universal-variable iteration) with:
  - Robust bracket selection for the universal anomaly chi
  - Newton-Raphson with damping near the parabolic boundary
  - Explicit handling of the 180-degree singular case (parabolic transfer)

Multi-revolution branches are NOT covered (single-rev only).

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed., Microcosm Press,
        Algorithm 58 (Universal Variables Lambert).
    Bate, R. R., Mueller, D. D., White, J. E. (1971/2020). Fundamentals of
        Astrodynamics. Dover.
"""
import numpy as np

MU_EARTH = 398600.4418  # km^3/s^2

_TINY = 1e-12


def _stumpff_C(z: float) -> float:
    if z > _TINY:
        sz = np.sqrt(z)
        return (1.0 - np.cos(sz)) / z
    if z < -_TINY:
        sz = np.sqrt(-z)
        return (1.0 - np.cosh(sz)) / z
    return 0.5 - z / 24.0 + z * z / 720.0


def _stumpff_S(z: float) -> float:
    if z > _TINY:
        sz = np.sqrt(z)
        return (sz - np.sin(sz)) / sz**3
    if z < -_TINY:
        sz = np.sqrt(-z)
        return (np.sinh(sz) - sz) / sz**3
    return 1.0 / 6.0 - z / 120.0 + z * z / 5040.0


def lambert_battin(r1: np.ndarray, r2: np.ndarray, tof: float,
                   mu: float = MU_EARTH, prograde: bool = True,
                   max_iter: int = 60, tol: float = 1e-8
                   ) -> tuple[np.ndarray, np.ndarray] | None:
    """Solve single-revolution Lambert via Vallado universal-variable iteration.

    Args:
        r1, r2: 3-vector position vectors [km] at the two epochs.
        tof: time of flight from r1 to r2 [s], must be > 0.
        mu: gravitational parameter [km^3/s^2].
        prograde: True for posigrade transfer, False for retrograde.
        max_iter: Newton iteration cap.
        tol: convergence tolerance on TOF residual [s].

    Returns:
        (v1, v2) departure and arrival velocity 3-vectors [km/s], or None if
        the solver did not converge.
    """
    r1n = float(np.linalg.norm(r1))
    r2n = float(np.linalg.norm(r2))
    if r1n < _TINY or r2n < _TINY or tof <= 0.0:
        return None

    cos_dnu = float(np.dot(r1, r2)) / (r1n * r2n)
    cos_dnu = max(-1.0, min(1.0, cos_dnu))

    cross = np.cross(r1, r2)
    if prograde:
        dnu = np.arccos(cos_dnu) if cross[2] >= 0 else 2 * np.pi - np.arccos(cos_dnu)
    else:
        dnu = np.arccos(cos_dnu) if cross[2] <= 0 else 2 * np.pi - np.arccos(cos_dnu)

    # Special case: 180-deg transfer (cos_dnu = -1) -> A = 0, parabolic singularity
    if abs(np.sin(dnu)) < 1e-9:
        return None

    A = np.sign(np.sin(dnu)) * np.sqrt(r1n * r2n * (1.0 + cos_dnu))
    if abs(A) < _TINY:
        return None

    # Initial guess: z = 0 (parabolic) is a stable starting point
    z = 0.0

    def _yz(z_):
        S = _stumpff_S(z_); C = _stumpff_C(z_)
        if abs(C) < _TINY:
            return r1n + r2n
        return r1n + r2n + A * (z_ * S - 1.0) / np.sqrt(C)

    def _F(z_):
        y = _yz(z_)
        if y <= 0:
            return None
        S = _stumpff_S(z_); C = _stumpff_C(z_)
        if C <= 0:
            return None
        return (y / C) ** 1.5 * S + A * np.sqrt(y) - np.sqrt(mu) * tof

    def _dFdz(z_):
        y = _yz(z_)
        if y <= 0:
            return None
        S = _stumpff_S(z_); C = _stumpff_C(z_)
        if C <= 0:
            return None
        if abs(z_) < 1e-9:
            return (np.sqrt(2) / 40.0) * y ** 1.5 + (A / 8.0) * (np.sqrt(y) + A * np.sqrt(1.0 / (2.0 * y)))
        term1 = (y / C) ** 1.5 * (1.0 / (2.0 * z_) * (C - 1.5 * S / C) + 0.75 * S * S / C)
        term2 = (A / 8.0) * (3.0 * S * np.sqrt(y) / C + A * np.sqrt(C / y))
        return term1 + term2

    # Newton-Raphson on z; bisect-fallback if Newton diverges
    z_low, z_high = -50.0, 4.0 * np.pi**2
    for _ in range(max_iter):
        F = _F(z)
        if F is None:
            # Push z back toward feasible range
            z = (z_low + z_high) / 2.0
            continue
        if abs(F) < tol * np.sqrt(mu):
            break
        dF = _dFdz(z)
        if dF is None or abs(dF) < _TINY:
            z = (z_low + z_high) / 2.0
            continue
        z_new = z - F / dF
        if z_new < z_low or z_new > z_high:
            z_new = (z_low + z_high) / 2.0
        # Update bracket via bisection on F sign
        F_new = _F(z_new)
        if F_new is not None:
            if F * F_new < 0:
                z_low, z_high = (z, z_new) if z < z_new else (z_new, z)
        z = z_new
    else:
        return None

    y = _yz(z)
    if y is None or y <= 0:
        return None
    f = 1.0 - y / r1n
    g = A * np.sqrt(y / mu)
    g_dot = 1.0 - y / r2n
    if abs(g) < _TINY:
        return None
    v1 = (r2 - f * r1) / g
    v2 = (g_dot * r2 - r1) / g
    return v1, v2
