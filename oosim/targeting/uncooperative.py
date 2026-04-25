"""Non-cooperative tumbling target — UKF skeleton + adaptive QP hook.

This is a PLACEHOLDER for the A1 journal extension (planned April 2027). The
IAC paper does not report any results from this module; it is included in the
open release to signal the intended trajectory of the work and to provide a
stable interface for downstream collaborators.

References (intent):
    Park, T. H. & D'Amico, S. (2022). SPEED+: Pose Estimation Dataset across
        Domain Gap. IEEE Aerospace. DOI: 10.1109/AERO53065.2022.9843439
    Virgili-Llop, J. & Romano, M. (2019). Simultaneous Capture and Detumble of
        a Resident Space Object by a Free-Flying Spacecraft with a Robotic Arm.
        Frontiers in Robotics and AI. DOI: 10.3389/frobt.2019.00014
    Nanos, K. & Papadopoulos, E. (2017). On the Dynamics and Control of
        Free-floating Space Manipulator Systems. Frontiers in Robotics and AI.
        DOI: 10.3389/frobt.2017.00026
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class TumblingTargetEstimate:
    """UKF state estimate for a non-cooperative tumbling target.

    State vector (15-dim):
        [r_rel(3), v_rel(3), omega_target(3), inertia_diag(3), bias(3)]
    """
    pos_rel: np.ndarray             # 3-vector chaser-to-target position [m]
    vel_rel: np.ndarray             # 3-vector relative velocity [m/s]
    omega_target: np.ndarray        # 3-vector target angular velocity [rad/s]
    inertia_diag: np.ndarray        # 3-vector diagonal inertia [kg.m^2]
    sensor_bias: np.ndarray         # 3-vector LIDAR/camera systematic bias
    covariance: np.ndarray          # 15x15 state covariance matrix


def predict_capture_window(estimate: TumblingTargetEstimate,
                           horizon_s: float,
                           grasping_geometry_target: np.ndarray) -> np.ndarray:
    """Predict the time-varying graspable window for a tumbling target.

    For a target rotating with angular velocity ω, a fixed grasping fixture
    on the target sweeps through the inertial frame at the same rate. The
    chaser must arrive at the right pose at the right phase of the rotation.

    NOT IMPLEMENTED. Stub for A1 journal extension.

    Args:
        estimate: current UKF estimate of target state.
        horizon_s: prediction horizon in seconds.
        grasping_geometry_target: 3-vector position of grasping fixture in
            target body frame.

    Returns:
        Predicted (time-stamped) sequence of admissible chaser poses.
    """
    raise NotImplementedError(
        "Non-cooperative tumbling target capture is reserved for the A1 "
        "journal extension (April 2027). This stub exists for API stability."
    )


def ukf_update_step(*args, **kwargs) -> TumblingTargetEstimate:
    """Unscented Kalman Filter measurement update.

    NOT IMPLEMENTED. Stub for A1 journal extension.

    Will implement the standard UKF (Julier & Uhlmann 1997) on the 15-dim
    augmented state vector, with sigma-point parameters tuned for the
    process and measurement noise levels documented in Park & D'Amico
    (SPEED+ 2022) and Virgili-Llop & Romano (2019).
    """
    raise NotImplementedError(
        "UKF update step is a stub for the A1 journal extension."
    )
