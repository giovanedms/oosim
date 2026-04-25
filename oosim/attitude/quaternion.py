"""Quaternion kinematics and rigid-body attitude dynamics.

Convention: scalar-last [qx, qy, qz, qw].
References:
    Sidi, M. J. (1997). Spacecraft Dynamics and Control. Cambridge UP.
    Wertz et al. (2011). Space Mission Engineering: The New SMAD.
"""
import numpy as np


def quat_normalize(q: np.ndarray) -> np.ndarray:
    return q / np.linalg.norm(q)


def quat_mult(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product q1 ⊗ q2 (scalar-last)."""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    ])


def quat_kinematics_rate(q: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """Time derivative q_dot = 0.5 * q ⊗ [omega, 0]."""
    omega_q = np.concatenate([omega, [0.0]])
    return 0.5 * quat_mult(q, omega_q)


def euler_dynamics(omega: np.ndarray, torque: np.ndarray, inertia: np.ndarray) -> np.ndarray:
    """Rigid-body angular acceleration: omega_dot = I^-1 (M - omega x I omega).

    Args:
        omega: 3-vector angular velocity [rad/s].
        torque: 3-vector applied torque [N.m].
        inertia: 3x3 inertia tensor [kg.m^2].

    Returns:
        omega_dot 3-vector [rad/s^2].
    """
    return np.linalg.solve(inertia, torque - np.cross(omega, inertia @ omega))
