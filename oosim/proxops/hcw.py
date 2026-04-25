"""Hill-Clohessy-Wiltshire (HCW) linearized relative motion.

References:
    Clohessy, W. H. & Wiltshire, R. S. (1960). Terminal Guidance System for
        Satellite Rendezvous. J. Aerospace Sci. 27(9):653-658. DOI: 10.2514/8.8704
    Sullivan, Grimberg, D'Amico (2017). Comprehensive Survey and Assessment of
        Spacecraft Relative Motion Dynamics Models. JGCD. DOI: 10.2514/1.G002309
"""
import numpy as np

MU_EARTH = 398600.4418  # km^3/s^2


def mean_motion(semi_major_axis_km: float, mu: float = MU_EARTH) -> float:
    """Mean motion n = sqrt(mu / a^3) [rad/s]."""
    return float(np.sqrt(mu / semi_major_axis_km**3))


def hcw_state_transition_matrix(n: float, t: float) -> np.ndarray:
    """Closed-form 6x6 STM for force-free HCW dynamics.

    State vector ordering: [x, y, z, x_dot, y_dot, z_dot] in LVLH frame
    (x = R-bar radial, y = along-track, z = cross-track).

    Args:
        n: mean motion of target orbit [rad/s].
        t: elapsed time [s].

    Returns:
        Phi: 6x6 numpy array.
    """
    nt = n * t
    s, c = np.sin(nt), np.cos(nt)
    phi = np.array([
        [4 - 3*c,        0, 0,  s/n,         2*(1-c)/n,  0],
        [6*(s - nt),     1, 0, -2*(1-c)/n,  (4*s - 3*nt)/n, 0],
        [0,              0, c,  0,           0,          s/n],
        [3*n*s,          0, 0,  c,           2*s,        0],
        [-6*n*(1-c),     0, 0, -2*s,         4*c - 3,    0],
        [0,              0, -n*s, 0,         0,          c],
    ])
    return phi


def propagate_hcw(state0: np.ndarray, n: float, t: float) -> np.ndarray:
    """Propagate force-free HCW state by time t.

    Args:
        state0: initial 6-vector [x, y, z, x_dot, y_dot, z_dot].
        n: mean motion [rad/s].
        t: elapsed time [s].

    Returns:
        State at time t.
    """
    return hcw_state_transition_matrix(n, t) @ state0
