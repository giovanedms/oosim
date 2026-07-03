"""Lambert problem solver — Izzo (2015) algorithm, single revolution.

Robust single-revolution Lambert solver via Izzo's Householder iteration on
the time-of-flight equation parameterized by the variable x. Compared to
the universal-variable formulation, Izzo's parametrization is numerically
well-behaved across elliptic, parabolic and hyperbolic transfers.

The time-of-flight curve T(x) uses the Lancaster-Blanchard form away from
x = 1 (Lagrange form in the mid-range), and the Battin hypergeometric series
near the parabolic point x = 1, following Izzo (2015) Section 4. The root is
found with a third-order Householder iteration using the analytic derivatives
dT/dx, d2T/dx2, d3T/dx3 (Izzo eq. 22).

This is a single-revolution implementation; multi-revolution branches
(M >= 1) are not covered.

Reference:
    Izzo, D. (2015). Revisiting Lambert's problem. Celestial Mechanics and
        Dynamical Astronomy 121(1):1-15. DOI: 10.1007/s10569-014-9587-y
"""
import numpy as np

MU_EARTH = 398600.4418

_TINY = 1e-9


def _hyp2f1b(z: float) -> float:
    """Gauss hypergeometric function 2F1(3, 1; 5/2; z) by direct series.

    Converges for z < 1; used only in the Battin series branch of _x2tof
    where z = S1 is small (near-parabolic region).
    """
    if z >= 1.0:
        return np.inf
    Sj = 1.0
    Cj = 1.0
    j = 0
    while True:
        Cj *= (3.0 + j) * (1.0 + j) / (2.5 + j) * z / (j + 1.0)
        Sj_new = Sj + Cj
        if Sj_new == Sj:
            return Sj
        Sj = Sj_new
        j += 1


def _x2tof(x: float, ll: float) -> float:
    """Non-dimensional time of flight T(x) for M = 0 (Izzo 2015, Section 4).

    Three regimes for numerical robustness:
      |x - 1| < 0.01          -> Battin hypergeometric series (near-parabolic)
      0.01 <= |x - 1| < 0.2   -> Lagrange form (alpha/beta angles)
      |x - 1| >= 0.2          -> Lancaster-Blanchard form
    """
    battin_gap = 0.01
    lagrange_gap = 0.2
    dist = abs(x - 1.0)

    if battin_gap <= dist < lagrange_gap:
        # Lagrange form
        a = 1.0 / (1.0 - x * x)
        if a > 0:
            # Elliptic
            alfa = 2.0 * np.arccos(np.clip(x, -1.0, 1.0))
            beta = 2.0 * np.arcsin(np.sqrt(ll * ll / a))
            if ll < 0.0:
                beta = -beta
            return a * np.sqrt(a) * ((alfa - np.sin(alfa))
                                     - (beta - np.sin(beta))) / 2.0
        # Hyperbolic
        alfa = 2.0 * np.arccosh(x)
        beta = 2.0 * np.arcsinh(np.sqrt(-ll * ll / a))
        if ll < 0.0:
            beta = -beta
        return -a * np.sqrt(-a) * ((beta - np.sinh(beta))
                                   - (alfa - np.sinh(alfa))) / 2.0

    K = ll * ll
    E = x * x - 1.0
    rho = abs(E)
    z = np.sqrt(1.0 + K * E)

    if dist < battin_gap:
        # Battin series (near-parabolic, includes x = 1 exactly)
        eta = z - ll * x
        S1 = 0.5 * (1.0 - ll - x * eta)
        Q = (4.0 / 3.0) * _hyp2f1b(S1)
        return 0.5 * (eta ** 3 * Q + 4.0 * ll * eta)

    # Lancaster-Blanchard form
    y = np.sqrt(rho)
    g = x * z - ll * E
    if E < 0:
        d = np.arccos(np.clip(g, -1.0, 1.0))
    else:
        d = np.log(max(y * (z - ll * x) + g, _TINY * _TINY))
    return (x - ll * z - d / y) / E


def _dTdx(x: float, T: float, ll: float) -> tuple[float, float, float]:
    """Analytic derivatives dT/dx, d2T/dx2, d3T/dx3 (Izzo 2015, eq. 22)."""
    l2 = ll * ll
    l3 = l2 * ll
    umx2 = 1.0 - x * x
    y = np.sqrt(1.0 - l2 * umx2)
    y3 = y * y * y
    y5 = y3 * y * y
    DT = (3.0 * T * x - 2.0 + 2.0 * l3 * x / y) / umx2
    DDT = (3.0 * T + 5.0 * x * DT + 2.0 * (1.0 - l2) * l3 / y3) / umx2
    DDDT = (7.0 * x * DDT + 8.0 * DT
            - 6.0 * (1.0 - l2) * l2 * l3 * x / y5) / umx2
    return DT, DDT, DDDT


def _initial_guess(T: float, ll: float) -> float:
    """Izzo's initial guess for x, M = 0 (eq. 30 in the paper)."""
    T0 = np.arccos(ll) + ll * np.sqrt(1.0 - ll * ll)  # T(x=0)
    T1 = (2.0 / 3.0) * (1.0 - ll ** 3)                # T(x=1), parabolic
    if T >= T0:
        x0 = (T0 / T) ** (2.0 / 3.0) - 1.0
    elif T < T1:
        x0 = 2.5 * T1 * (T1 - T) / ((1.0 - ll ** 5) * T) + 1.0
    else:
        x0 = np.exp(np.log(2.0) * np.log(T / T0) / np.log(T1 / T0)) - 1.0
    return float(x0)


def lambert_izzo(r1: np.ndarray, r2: np.ndarray, tof: float,
                 mu: float = MU_EARTH, prograde: bool = True,
                 max_iter: int = 30, tol: float = 1e-11
                 ) -> tuple[np.ndarray, np.ndarray] | None:
    """Solve single-revolution Lambert via Izzo's algorithm.

    Args:
        r1, r2: 3-vector position vectors [km] at the two epochs.
        tof: time of flight [s], must be > 0.
        mu: gravitational parameter [km^3/s^2].
        prograde: True for posigrade transfer, False for retrograde.
        max_iter: Householder iteration cap.
        tol: convergence tolerance on the iterate x.

    Returns:
        (v1, v2) velocity 3-vectors [km/s], or None if the geometry is
        degenerate (zero radius, collinear endpoints) or the solver did
        not converge.
    """
    r1 = np.asarray(r1, dtype=float)
    r2 = np.asarray(r2, dtype=float)
    r1n = float(np.linalg.norm(r1))
    r2n = float(np.linalg.norm(r2))
    if r1n < _TINY or r2n < _TINY or tof <= 0.0:
        return None

    c_vec = r2 - r1
    c = float(np.linalg.norm(c_vec))
    if c < _TINY:
        return None
    s = 0.5 * (r1n + r2n + c)

    ir1 = r1 / r1n
    ir2 = r2 / r2n
    ih = np.cross(ir1, ir2)
    ihn = float(np.linalg.norm(ih))
    if ihn < _TINY:
        # Collinear endpoints (0 or 180 deg): transfer plane is undefined
        return None
    ih = ih / ihn

    # ll (lambda in Izzo's notation); sign flips for transfer angle > pi
    ll = np.sqrt(max(0.0, 1.0 - c / s))
    if ih[2] < 0.0:
        # Transfer angle > 180 deg as seen from +z
        ll = -ll
        it1 = np.cross(ir1, ih)
        it2 = np.cross(ir2, ih)
    else:
        it1 = np.cross(ih, ir1)
        it2 = np.cross(ih, ir2)
    if not prograde:
        ll = -ll
        it1 = -it1
        it2 = -it2

    # Non-dimensional TOF (Izzo eq. 6)
    T = np.sqrt(2.0 * mu / s ** 3) * tof

    # Householder third-order iteration on T(x) - T = 0
    x = _initial_guess(T, ll)
    converged = False
    for _ in range(max_iter):
        Tx = _x2tof(x, ll)
        DT, DDT, DDDT = _dTdx(x, Tx, ll)
        delta = Tx - T
        DT2 = DT * DT
        denom = DT * (DT2 - delta * DDT) + DDDT * delta * delta / 6.0
        if abs(denom) < 1e-300:
            return None
        x_new = x - delta * (DT2 - 0.5 * delta * DDT) / denom
        if abs(x_new - x) < tol:
            x = x_new
            converged = True
            break
        x = x_new
    if not converged:
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

    v1 = Vr1 * ir1 + Vt1 * it1
    v2 = Vr2 * ir2 + Vt2 * it2
    return v1, v2
