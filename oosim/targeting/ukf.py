"""Unscented Kalman Filter for relative-state estimation in proximity operations.

Implements the Julier-Uhlmann UKF for the 6-dim HCW relative state
[x, y, z, vx, vy, vz] in LVLH frame, with linear measurement model
(sensor measures relative position; velocity is unobserved and reconstructed
from the dynamics + measurement history).

This is the missing piece identified by the MPC tuning sweep failure
(Section 5.4.1) — the state estimator upstream of the QP that filters
high-frequency sensor noise before the optimizer sees it.

For the IAC paper, this module enables a NEW Monte Carlo (UKF + MPC closed-loop)
that is expected to recover useful success rates by filtering measurement noise.
The UKF will be used as the central methodological contribution of the A1
journal extension when combined with non-cooperative pose estimation.

Reference:
    Julier, S. J. & Uhlmann, J. K. (1997). A new extension of the Kalman filter
        to nonlinear systems. Proc. SPIE 3068, Signal Processing, Sensor Fusion,
        and Target Recognition VI. (Foundational UKF paper.)
"""
from dataclasses import dataclass
import numpy as np

from ..proxops.hcw import hcw_state_transition_matrix


@dataclass
class UKFState:
    """UKF estimate of the 6-dim relative state in LVLH."""
    mean: np.ndarray           # (6,) state mean [m, m/s]
    cov: np.ndarray            # (6,6) state covariance


def _generate_sigma_points(mean: np.ndarray, cov: np.ndarray,
                           alpha: float = 1e-3, beta: float = 2.0,
                           kappa: float = 0.0
                           ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Standard scaled sigma-point generator (Julier-Uhlmann)."""
    n = mean.size
    lam = alpha**2 * (n + kappa) - n
    gamma = np.sqrt(n + lam)

    # Cholesky of (n + lam) * cov
    try:
        L = np.linalg.cholesky((n + lam) * cov)
    except np.linalg.LinAlgError:
        # Add small jitter for numerical stability
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


def ukf_predict(state: UKFState, n_motion: float, dt: float,
                process_noise_cov: np.ndarray) -> UKFState:
    """UKF predict step under HCW linear dynamics.

    Although HCW is linear (so the UKF reduces to Kalman filter for prediction),
    we implement it via sigma points for symmetry with the measurement update
    and to support future nonlinear extensions (J2-perturbed HCW, attitude coupling).

    Args:
        state: prior UKFState.
        n_motion: target orbit mean motion [rad/s].
        dt: timestep [s].
        process_noise_cov: 6x6 additive process noise covariance.

    Returns:
        UKFState after prediction.
    """
    sigmas, Wm, Wc = _generate_sigma_points(state.mean, state.cov)
    Phi = hcw_state_transition_matrix(n_motion, dt)
    sigmas_pred = sigmas @ Phi.T

    mean_pred = (Wm[:, None] * sigmas_pred).sum(axis=0)
    diff = sigmas_pred - mean_pred
    cov_pred = (Wc[:, None, None] * diff[:, :, None] * diff[:, None, :]).sum(axis=0)
    cov_pred = cov_pred + process_noise_cov
    return UKFState(mean=mean_pred, cov=cov_pred)


def ukf_update(state: UKFState, measurement: np.ndarray,
               measurement_noise_cov: np.ndarray) -> UKFState:
    """UKF measurement update with linear position observation H = [I_3 | 0].

    Args:
        state: predicted UKFState.
        measurement: 3-vector measured relative position [m].
        measurement_noise_cov: 3x3 measurement noise covariance.

    Returns:
        UKFState after update.
    """
    sigmas, Wm, Wc = _generate_sigma_points(state.mean, state.cov)
    # Measurement function: h(x) = x[:3] (position observation)
    z_sigmas = sigmas[:, :3]
    z_pred = (Wm[:, None] * z_sigmas).sum(axis=0)
    dz = z_sigmas - z_pred
    Pz = (Wc[:, None, None] * dz[:, :, None] * dz[:, None, :]).sum(axis=0) + measurement_noise_cov
    dx = sigmas - state.mean
    Pxz = (Wc[:, None, None] * dx[:, :, None] * dz[:, None, :]).sum(axis=0)

    K = Pxz @ np.linalg.inv(Pz)
    innovation = measurement - z_pred
    new_mean = state.mean + K @ innovation
    new_cov = state.cov - K @ Pz @ K.T
    # Symmetrize for numerical stability
    new_cov = 0.5 * (new_cov + new_cov.T)
    return UKFState(mean=new_mean, cov=new_cov)
