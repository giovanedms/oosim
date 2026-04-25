"""Vision-based relative pose estimation simulator (stub for A1 extension).

For non-cooperative targets without retro-reflectors, the chaser must estimate
the target's relative pose from monocular or stereo camera imagery. The
state-of-the-art uses convolutional neural networks trained on synthetic
imagery (SPEED+ benchmark of Park & D'Amico 2022) with a sim-to-real domain
gap penalty.

This module provides a minimal forward model: given the true relative pose,
return a noisy observation consistent with the documented accuracy of
operational LIDAR + vision systems. Full pose estimation (CNN inference
on rendered imagery) is reserved for the A1 journal extension.

Reference:
    Park, T. H. & D'Amico, S. (2022). SPEED+: Next-Generation Dataset for
        Spacecraft Pose Estimation across Domain Gap. IEEE Aerospace.
        DOI: 10.1109/AERO53065.2022.9843439
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class VisionSensorSpec:
    """Sensor noise specification documented for typical OOS sensors."""
    range_m: float                   # operating range to target [m]
    sigma_pos_per_meter: float       # position noise [m] per meter of range
    sigma_pos_floor_m: float         # noise floor at zero range [m]
    sigma_quat: float                # attitude noise [rad] (1-sigma per axis)
    label: str = ""


# Documented operational sensors (approximate from public specifications).
LIDAR_TRIDAR_SHORT = VisionSensorSpec(
    range_m=200.0, sigma_pos_per_meter=1.5e-4, sigma_pos_floor_m=0.005,
    sigma_quat=np.deg2rad(0.5), label="TriDAR Neptec (Cygnus, 200 m)",
)
LIDAR_RVS_LONG = VisionSensorSpec(
    range_m=5000.0, sigma_pos_per_meter=5e-4, sigma_pos_floor_m=0.05,
    sigma_quat=np.deg2rad(1.0), label="RVS JenaOptronik (HTV, 5 km)",
)
DRAGON_EYE = VisionSensorSpec(
    range_m=300.0, sigma_pos_per_meter=2e-4, sigma_pos_floor_m=0.010,
    sigma_quat=np.deg2rad(0.3), label="DragonEye thermal LIDAR (Crew Dragon)",
)


def measure_pose(true_pos: np.ndarray, true_quat: np.ndarray,
                 sensor: VisionSensorSpec, rng) -> tuple[np.ndarray, np.ndarray]:
    """Forward measurement model: add Gaussian noise to true pose."""
    r = float(np.linalg.norm(true_pos))
    sigma = sensor.sigma_pos_floor_m + sensor.sigma_pos_per_meter * r
    pos_meas = true_pos + rng.normal(0, sigma, 3)
    quat_meas = true_quat + rng.normal(0, sensor.sigma_quat, 4)
    quat_meas = quat_meas / np.linalg.norm(quat_meas)
    return pos_meas, quat_meas
