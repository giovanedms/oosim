"""Capture envelope formalization: target manipulator workspace + attitude bounds + rate caps.

This is contribution I2 of the IAC paper. The capture envelope is a convex set in
the joint position-attitude-rate space, defining where the chaser must be at
terminal time for the target's manipulator to grasp.

To preserve QP convexity, non-convex workspaces (typical for articulated arms with
joint limits and singularities) are approximated by a maximal inner ellipsoid.

Reference: Tobenkin, Manchester, Tedrake (2011). Invariant Funnels around
Trajectories using Sum-of-Squares Programming. IFAC. DOI: 10.3182/20110828-6-it-1002.03098
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class CaptureEnvelope:
    """Convex capture envelope for berthing-compatible terminal conditions.

    Workspace is approximated as an axis-aligned ellipsoid centered at `center_pos`
    with semi-axes `pos_semi_axes`. Attitude is constrained to lie within
    `att_tolerance_rad` of `target_quat`. Residual rates are bounded above
    by `vel_max` and `omega_max`.
    """
    center_pos: np.ndarray         # 3-vector [m] in LVLH
    pos_semi_axes: np.ndarray      # 3-vector [m]
    target_quat: np.ndarray        # 4-vector (scalar-last)
    att_tolerance_rad: float       # max angular deviation [rad]
    vel_max: float = 0.05          # |v_rel| bound [m/s], default 5 cm/s
    omega_max: float = 0.0017      # |omega_rel| bound [rad/s], default 0.1 deg/s

    def contains(self, pos: np.ndarray, quat: np.ndarray,
                 vel: np.ndarray, omega: np.ndarray) -> bool:
        """Test whether (pos, quat, vel, omega) lies inside the envelope."""
        pos_err = (pos - self.center_pos) / self.pos_semi_axes
        if np.dot(pos_err, pos_err) > 1.0:
            return False
        att_err_dot = abs(np.dot(quat, self.target_quat))
        if att_err_dot < np.cos(self.att_tolerance_rad / 2.0):
            return False
        if np.linalg.norm(vel) > self.vel_max:
            return False
        if np.linalg.norm(omega) > self.omega_max:
            return False
        return True
