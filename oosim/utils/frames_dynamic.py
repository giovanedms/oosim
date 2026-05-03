"""Dynamic ECI <-> LVLH transforms with frame angular velocity tracking.

Extends frames.py with time-aware and angular-velocity-coupled transforms for
proximity operations where the LVLH frame rotates non-trivially (eccentric orbits)
or where Coriolis coupling in the relative velocity must be accounted for.

Convention (same as frames.py, Vallado / Sullivan-Grimberg-D'Amico 2017):
    x_LVLH = R-bar (radial, pointing away from Earth)
    y_LVLH = V-bar (along-track, in direction of motion)
    z_LVLH = H-bar (orbit normal, completing right-handed triad)

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed.
    Sullivan, Grimberg, D'Amico (2017). Comprehensive Survey of Spacecraft
        Relative Motion Dynamics. JGCD. DOI: 10.2514/1.G002309
    Schaub, H., Junkins, J. L. (2018). Analytical Mechanics of Space Systems,
        3rd ed. AIAA. (Ch. 13, relative motion kinematics)
"""
import numpy as np
from typing import Callable, Tuple

from .frames import eci_to_lvlh_rotation

MU_EARTH: float = 398600.4418  # [km^3/s^2] — WGS84 GM


# ---------------------------------------------------------------------------
# 1. LVLH angular velocity
# ---------------------------------------------------------------------------

def lvlh_angular_velocity_in_eci(
    r_target_eci: np.ndarray,
    v_target_eci: np.ndarray,
    mu: float = MU_EARTH,
) -> np.ndarray:
    """Angular velocity vector of the LVLH frame expressed in ECI coordinates.

    For any Keplerian orbit (circular or eccentric):

        omega_eci = (r x v) / |r|^2

    This is exact for a two-body orbit — the z-component in LVLH equals the
    instantaneous mean motion n = sqrt(mu/r^3) only for a circular orbit; for
    eccentric orbits the magnitude varies with true anomaly.

    Args:
        r_target_eci: 3-vector position of target in ECI [km].
        v_target_eci: 3-vector velocity of target in ECI [km/s].
        mu: gravitational parameter [km^3/s^2]. Default = MU_EARTH.

    Returns:
        omega_eci: 3-vector angular velocity of LVLH frame in ECI [rad/s].
    """
    r_norm_sq = np.dot(r_target_eci, r_target_eci)
    h_vec = np.cross(r_target_eci, v_target_eci)  # specific angular momentum [km^2/s]
    return h_vec / r_norm_sq


# ---------------------------------------------------------------------------
# 2. ECI relative state → LVLH relative state (Coriolis-correct)
# ---------------------------------------------------------------------------

def eci_state_to_lvlh_relative(
    r_chaser_eci: np.ndarray,
    v_chaser_eci: np.ndarray,
    r_target_eci: np.ndarray,
    v_target_eci: np.ndarray,
    mu: float = MU_EARTH,
) -> np.ndarray:
    """Compute chaser relative state in LVLH with full Coriolis coupling.

    Derivation:
        dr_eci     = r_chaser - r_target
        dv_eci     = v_chaser - v_target   (ECI-frame time derivative)
        omega_eci  = (r_target x v_target) / |r_target|^2
        omega_lvlh = R @ omega_eci
        dr_lvlh    = R @ dr_eci
        dv_lvlh    = R @ dv_eci - omega_lvlh x dr_lvlh

    The cross-product term converts the ECI-frame relative velocity to the
    LVLH-frame time derivative (Coriolis correction for the rotating frame).

    Args:
        r_chaser_eci: 3-vector chaser position in ECI [km].
        v_chaser_eci: 3-vector chaser velocity in ECI [km/s].
        r_target_eci: 3-vector target position in ECI [km].
        v_target_eci: 3-vector target velocity in ECI [km/s].
        mu: gravitational parameter [km^3/s^2].

    Returns:
        rel_state: 6-vector [x, y, z, vx, vy, vz] in LVLH centered on target
                   [km, km/s].
    """
    R = eci_to_lvlh_rotation(r_target_eci, v_target_eci)

    dr_eci = r_chaser_eci - r_target_eci
    dv_eci = v_chaser_eci - v_target_eci

    omega_eci = lvlh_angular_velocity_in_eci(r_target_eci, v_target_eci, mu)
    omega_lvlh = R @ omega_eci

    dr_lvlh = R @ dr_eci
    dv_lvlh = R @ dv_eci - np.cross(omega_lvlh, dr_lvlh)

    return np.concatenate([dr_lvlh, dv_lvlh])


# ---------------------------------------------------------------------------
# 3. LVLH relative state → ECI absolute states (inverse)
# ---------------------------------------------------------------------------

def lvlh_relative_to_eci_state(
    rel_state_lvlh: np.ndarray,
    r_target_eci: np.ndarray,
    v_target_eci: np.ndarray,
    mu: float = MU_EARTH,
) -> Tuple[np.ndarray, np.ndarray]:
    """Inverse of eci_state_to_lvlh_relative — recover chaser ECI state.

    Given the target ECI state and the chaser relative state in LVLH, computes
    the chaser absolute state in ECI.

    Args:
        rel_state_lvlh: 6-vector [x, y, z, vx, vy, vz] in LVLH [km, km/s].
        r_target_eci: 3-vector target position in ECI [km].
        v_target_eci: 3-vector target velocity in ECI [km/s].
        mu: gravitational parameter [km^3/s^2].

    Returns:
        r_chaser_eci: 3-vector chaser position in ECI [km].
        v_chaser_eci: 3-vector chaser velocity in ECI [km/s].
    """
    R = eci_to_lvlh_rotation(r_target_eci, v_target_eci)
    R_inv = R.T  # rotation matrix — transpose = inverse

    dr_lvlh = rel_state_lvlh[:3]
    dv_lvlh = rel_state_lvlh[3:]

    omega_eci = lvlh_angular_velocity_in_eci(r_target_eci, v_target_eci, mu)
    omega_lvlh = R @ omega_eci

    # Undo Coriolis: dv_eci = R^T @ (dv_lvlh + omega_lvlh x dr_lvlh)
    dr_eci = R_inv @ dr_lvlh
    dv_eci = R_inv @ (dv_lvlh + np.cross(omega_lvlh, dr_lvlh))

    r_chaser_eci = r_target_eci + dr_eci
    v_chaser_eci = v_target_eci + dv_eci

    return r_chaser_eci, v_chaser_eci


# ---------------------------------------------------------------------------
# 4. High-level orbit tracker
# ---------------------------------------------------------------------------

def track_relative_along_orbit(
    chaser_initial_eci: np.ndarray,
    target_initial_eci: np.ndarray,
    t_array: np.ndarray,
    propagator_fn: Callable[[np.ndarray, float], np.ndarray],
) -> np.ndarray:
    """Track relative state (LVLH) over a time history by propagating both objects.

    Each object is propagated independently in ECI using `propagator_fn`, then
    the LVLH relative state is computed at each timestamp including Coriolis
    coupling.

    Args:
        chaser_initial_eci: 6-vector [r, v] chaser initial state in ECI [km, km/s].
        target_initial_eci: 6-vector [r, v] target initial state in ECI [km, km/s].
        t_array: 1-D array of N timestamps [s]. t_array[0] is treated as t=0.
        propagator_fn: callable(state_6, t) -> state_6 that propagates a 6-vector
                       ECI state from t=0 to time t [s]. Must handle t=0 (identity).

    Returns:
        rel_states: (N, 6) array of relative states in LVLH [km, km/s] at each
                    timestamp in t_array.
    """
    n = len(t_array)
    rel_states = np.empty((n, 6))

    for i, t in enumerate(t_array):
        chaser_eci = propagator_fn(chaser_initial_eci, float(t))
        target_eci = propagator_fn(target_initial_eci, float(t))

        r_chaser = chaser_eci[:3]
        v_chaser = chaser_eci[3:]
        r_target = target_eci[:3]
        v_target = target_eci[3:]

        rel_states[i] = eci_state_to_lvlh_relative(
            r_chaser, v_chaser, r_target, v_target
        )

    return rel_states
