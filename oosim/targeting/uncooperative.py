"""Non-cooperative tumbling target — UKF full implementation.

Augmented 9-dimensional state UKF that tracks the relative pose AND the
tumbling target's angular velocity, suitable as the input to a time-varying
QP terminal-targeting that adapts the capture envelope to the current
attitude phase of the target.

Reduced augmentation (vs the 15-dim sketch in earlier stub): inertia matrix
is treated as an external parameter rather than estimated, since for the
short timescales of the terminal phase it is observable only weakly.

State vector (9-dim):
    [r_rel(3), v_rel(3), omega_target(3)]   (LVLH relative + target spin in body)

Reference:
    Julier, S. J. & Uhlmann, J. K. (1997). A new extension of the Kalman
        filter to nonlinear systems. SPIE 3068.
"""
from dataclasses import dataclass
import numpy as np

from ..proxops.hcw import hcw_state_transition_matrix


@dataclass
class TumblingState:
    """UKF estimate for relative pose + target angular velocity."""
    mean: np.ndarray   # (9,) [r_rel(3), v_rel(3), omega_target(3)]
    cov: np.ndarray    # (9,9)


def _sigma_points(mean: np.ndarray, cov: np.ndarray,
                  alpha: float = 1e-3, beta: float = 2.0, kappa: float = 0.0):
    n = mean.size
    lam = alpha**2 * (n + kappa) - n
    try:
        L = np.linalg.cholesky((n + lam) * cov)
    except np.linalg.LinAlgError:
        L = np.linalg.cholesky((n + lam) * cov + 1e-12 * np.eye(n))
    sigmas = np.zeros((2 * n + 1, n))
    sigmas[0] = mean
    for i in range(n):
        sigmas[i + 1] = mean + L[:, i]
        sigmas[n + i + 1] = mean - L[:, i]
    Wm = np.full(2 * n + 1, 1.0 / (2.0 * (n + lam)))
    Wc = Wm.copy()
    Wm[0] = lam / (n + lam)
    Wc[0] = lam / (n + lam) + (1.0 - alpha**2 + beta)
    return sigmas, Wm, Wc


def _propagate_state(state: np.ndarray, n_motion: float, dt: float) -> np.ndarray:
    """Propagate one sigma point: HCW for relative state, free-spin for omega."""
    Phi = hcw_state_transition_matrix(n_motion, dt)
    out = state.copy()
    out[:6] = Phi @ state[:6]
    # Target angular velocity is free-spin (constant in body frame, ignoring
    # gravity gradient torque on this timescale)
    out[6:9] = state[6:9]
    return out


def tumbling_predict(state: TumblingState, n_motion: float, dt: float,
                     process_noise_cov: np.ndarray) -> TumblingState:
    """UKF predict step under HCW + free-spin dynamics."""
    sigmas, Wm, Wc = _sigma_points(state.mean, state.cov)
    sigmas_pred = np.array([_propagate_state(s, n_motion, dt) for s in sigmas])
    mean_pred = (Wm[:, None] * sigmas_pred).sum(axis=0)
    diff = sigmas_pred - mean_pred
    cov_pred = (Wc[:, None, None] * diff[:, :, None] * diff[:, None, :]).sum(axis=0)
    cov_pred = cov_pred + process_noise_cov
    return TumblingState(mean=mean_pred, cov=cov_pred)


def tumbling_update_pose_and_rate(state: TumblingState,
                                   pos_meas: np.ndarray,
                                   omega_meas: np.ndarray,
                                   measurement_noise_cov: np.ndarray
                                   ) -> TumblingState:
    """UKF update with position + angular-velocity measurements.

    Measurement vector (6-dim): [pos_rel(3), omega_target(3)].
    Position from vision/LIDAR; omega from gyro on the chaser observing
    the target via vision-based motion estimation.
    """
    sigmas, Wm, Wc = _sigma_points(state.mean, state.cov)
    z_sigmas = np.column_stack([sigmas[:, :3], sigmas[:, 6:9]])
    z_pred = (Wm[:, None] * z_sigmas).sum(axis=0)
    dz = z_sigmas - z_pred
    Pz = (Wc[:, None, None] * dz[:, :, None] * dz[:, None, :]).sum(axis=0) + measurement_noise_cov
    dx = sigmas - state.mean
    Pxz = (Wc[:, None, None] * dx[:, :, None] * dz[:, None, :]).sum(axis=0)
    K = Pxz @ np.linalg.inv(Pz)
    measurement = np.concatenate([pos_meas, omega_meas])
    innovation = measurement - z_pred
    new_mean = state.mean + K @ innovation
    new_cov = state.cov - K @ Pz @ K.T
    new_cov = 0.5 * (new_cov + new_cov.T)
    return TumblingState(mean=new_mean, cov=new_cov)


def predict_capture_window(state: TumblingState, horizon_s: float,
                            grasping_geometry_target_body: np.ndarray
                            ) -> dict:
    """Predict the time-varying graspable pose given current tumble state.

    Returns the predicted target-frame grasping fixture position over time,
    rotated by the integrated angular velocity. The QP terminal targeting
    can then aim at the predicted pose at the planned terminal time t_f.

    Args:
        state: UKF estimate.
        horizon_s: prediction horizon [s].
        grasping_geometry_target_body: 3-vector position of the grasping
            fixture in the target body frame.

    Returns:
        dict with 't' (sample times), 'pose_lvlh' (target-body grasping
        position in LVLH at each t), and 'uncertainty_3sigma' (1-sigma
        position uncertainty propagated through the rotation).
    """
    omega = state.mean[6:9]
    omega_norm = float(np.linalg.norm(omega))
    times = np.linspace(0.0, horizon_s, 30)
    poses = np.zeros((len(times), 3))
    for i, t in enumerate(times):
        if omega_norm > 1e-9:
            angle = omega_norm * t
            axis = omega / omega_norm
            # Rodrigues' formula
            K = np.array([[0, -axis[2], axis[1]],
                          [axis[2], 0, -axis[0]],
                          [-axis[1], axis[0], 0]])
            R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
            poses[i] = state.mean[:3] + R @ grasping_geometry_target_body
        else:
            poses[i] = state.mean[:3] + grasping_geometry_target_body
    # Uncertainty bound: position cov + omega-induced angular sweep
    pos_sigma = float(np.sqrt(np.trace(state.cov[:3, :3])))
    omega_sigma_rad_s = float(np.sqrt(np.trace(state.cov[6:9, 6:9])))
    return {
        "times": times,
        "poses_lvlh": poses,
        "uncertainty_3sigma_m": 3 * pos_sigma + 3 * omega_sigma_rad_s * horizon_s
                                  * float(np.linalg.norm(grasping_geometry_target_body)),
    }
