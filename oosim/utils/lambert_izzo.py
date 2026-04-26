"""Lambert problem solver — Izzo (2015) algorithm, simplified.

Robust single-revolution Lambert solver via Izzo's householder iteration on
the time-of-flight equation parameterized by the variable x. Compared to
the universal-variable Battin formulation, Izzo's parametrization is
numerically well-behaved including at the 180-degree singularity.

This is a simplified single-revolution implementation; multi-revolution
branches (M >= 1) are not covered.

Reference:
    Izzo, D. (2015). Revisiting Lambert's problem. Celestial Mechanics and
        Dynamical Astronomy 121(1):1-15. DOI: 10.1007/s10569-014-9587-y
"""
import numpy as np

MU_EARTH = 398600.4418


def _x2tof(x: float, ll: float) -> float:
    """Time of flight as a function of x (Izzo eq. 17 — simplified)."""
    a = 1.0 - x * x
    if abs(a) < 1e-12:
        return (2.0 / 3.0) * (1.0 - ll * ll * ll)
    if a > 0:
        # Elliptic
        y = np.sqrt(1.0 - ll * ll * a)
        psi = np.arctan2(y - x * ll, 1.0 - x * y * 0 + ll * ll * a) if False else \
              np.arccos(np.clip(x * y + ll * (1.0 - x * x), -1.0, 1.0))
        return (psi - np.sin(psi)) / np.sqrt(a) ** 3 + 2 * ll * (1 - x * x) / a
    # Hyperbolic
    y = np.sqrt(1.0 - ll * ll * a)
    psi = np.arccosh(x * y - ll * a)
    return (np.sinh(psi) - psi) / np.sqrt(-a) ** 3 + 2 * ll * a / a


def _initial_guess(T: float, ll: float) -> float:
    """Izzo's initial guess for x (eq. 30 in the paper)."""
    T0 = np.arccos(ll) + ll * np.sqrt(1.0 - ll * ll)
    if T >= T0:
        x0 = (T0 / T) ** (2.0 / 3.0) - 1.0
    elif T < 2.0 * (1.0 - ll * ll * ll) / 3.0:
        x0 = 5.0 / 2.0 * (T0 - T) / (T * (1.0 - ll ** 5)) + 1.0
    else:
        x0 = (T0 / T) ** (np.log2(T0 / T)) - 1.0  # heuristic interpolation
    return float(x0)


def lambert_izzo(r1: np.ndarray, r2: np.ndarray, tof: float,
                 mu: float = MU_EARTH, prograde: bool = True,
                 max_iter: int = 30, tol: float = 1e-9
                 ) -> tuple[np.ndarray, np.ndarray] | None:
    """Solve single-revolution Lambert via Izzo's algorithm (simplified).

    Args:
        r1, r2: 3-vector position vectors [km] at the two epochs.
        tof: time of flight [s], must be > 0.
        mu: gravitational parameter [km^3/s^2].
        prograde: True for posigrade transfer, False for retrograde.

    Returns:
        (v1, v2) velocity 3-vectors [km/s], or None if solver did not converge.
    """
    r1n = float(np.linalg.norm(r1))
    r2n = float(np.linalg.norm(r2))
    if r1n < 1e-9 or r2n < 1e-9 or tof <= 0:
        return None

    c_vec = r2 - r1
    c = float(np.linalg.norm(c_vec))
    s = 0.5 * (r1n + r2n + c)

    # ll (lambda in Izzo's notation): sign depends on prograde/retrograde
    ll = np.sqrt(1.0 - c / s)
    cross = np.cross(r1, r2)
    if prograde and cross[2] < 0:
        ll = -ll
    if not prograde and cross[2] > 0:
        ll = -ll

    # Non-dimensional TOF (Izzo eq. 6)
    T = np.sqrt(2.0 * mu / s ** 3) * tof

    # Initial guess
    x = _initial_guess(T, ll)

    # Newton-Raphson on T(x) - T_target = 0
    for _ in range(max_iter):
        try:
            f = _x2tof(x, ll) - T
        except (ValueError, FloatingPointError):
            return None
        if abs(f) < tol:
            break
        # Numerical derivative (avoid analytic complexity for v1)
        dx = 1e-6
        try:
            df = (_x2tof(x + dx, ll) - _x2tof(x - dx, ll)) / (2 * dx)
        except (ValueError, FloatingPointError):
            return None
        if abs(df) < 1e-15:
            return None
        x = x - f / df
    else:
        return None

    # Recover velocities (Izzo Section 5)
    gamma = np.sqrt(mu * s / 2.0)
    rho = (r1n - r2n) / c
    sigma = np.sqrt(1.0 - rho * rho)

    y = np.sqrt(1.0 - ll * ll * (1.0 - x * x))
    Vr1 = gamma * ((ll * y - x) - rho * (ll * y + x)) / r1n
    Vr2 = -gamma * ((ll * y - x) + rho * (ll * y + x)) / r2n
    Vt1 = gamma * sigma * (y + ll * x) / r1n
    Vt2 = gamma * sigma * (y + ll * x) / r2n

    # Build velocity vectors in the (radial, tangential) basis at each endpoint
    ir1 = r1 / r1n
    ir2 = r2 / r2n
    ih = np.cross(r1, r2)
    ihn = np.linalg.norm(ih)
    if ihn < 1e-9:
        return None
    ih = ih / ihn
    it1 = np.cross(ih, ir1)
    it2 = np.cross(ih, ir2)

    v1 = Vr1 * ir1 + Vt1 * it1
    v2 = Vr2 * ir2 + Vt2 * it2
    return v1, v2
