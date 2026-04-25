"""Coordinate frame transforms: ECI <-> LVLH/RTN.

LVLH (Local Vertical Local Horizontal) and RTN (Radial-Transverse-Normal) are
two equivalent target-centered rotating frames widely used in proximity operations.

Convention used here (matches Vallado and Sullivan-Grimberg-D'Amico 2017):
    x_LVLH = R-bar (anti-radial, pointing away from Earth)
    y_LVLH = V-bar (along-track, in the direction of motion)
    z_LVLH = H-bar (orbit normal, completing right-handed triad)

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed.
    Sullivan, Grimberg, D'Amico (2017). Comprehensive Survey of Spacecraft
        Relative Motion Dynamics. JGCD. DOI: 10.2514/1.G002309
"""
import numpy as np


def eci_to_lvlh_rotation(r_target_eci: np.ndarray, v_target_eci: np.ndarray) -> np.ndarray:
    """Rotation matrix from ECI to LVLH (target-centered).

    Args:
        r_target_eci: 3-vector position of target in ECI [km].
        v_target_eci: 3-vector velocity of target in ECI [km/s].

    Returns:
        R_eci_to_lvlh: 3x3 rotation matrix such that v_LVLH = R @ v_ECI.
    """
    r_hat = r_target_eci / np.linalg.norm(r_target_eci)
    h = np.cross(r_target_eci, v_target_eci)
    h_hat = h / np.linalg.norm(h)
    y_hat = np.cross(h_hat, r_hat)  # along-track
    return np.vstack([r_hat, y_hat, h_hat])


def relative_state_eci_to_lvlh(r_chaser_eci: np.ndarray, v_chaser_eci: np.ndarray,
                                r_target_eci: np.ndarray, v_target_eci: np.ndarray
                                ) -> np.ndarray:
    """Compute relative state of chaser w.r.t. target in LVLH frame.

    Returns:
        6-vector [x, y, z, x_dot, y_dot, z_dot] in LVLH centered on target.
    """
    R = eci_to_lvlh_rotation(r_target_eci, v_target_eci)
    dr_eci = r_chaser_eci - r_target_eci
    dv_eci = v_chaser_eci - v_target_eci

    # Target angular velocity (rotation of LVLH frame in ECI):
    h = np.cross(r_target_eci, v_target_eci)
    omega = h / np.dot(r_target_eci, r_target_eci)  # n*z_hat for circular orbit
    omega_lvlh = R @ omega

    dr_lvlh = R @ dr_eci
    dv_lvlh = R @ dv_eci - np.cross(omega_lvlh, dr_lvlh)
    return np.concatenate([dr_lvlh, dv_lvlh])
