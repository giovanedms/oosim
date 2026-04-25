"""Tests for vision-based pose estimation forward model."""
import numpy as np
from oosim.targeting.vision_pose import (
    measure_pose, LIDAR_TRIDAR_SHORT, LIDAR_RVS_LONG, DRAGON_EYE,
)


def test_measure_pose_zero_noise_at_zero_range():
    rng = np.random.default_rng(0)
    spec = type(LIDAR_TRIDAR_SHORT)(
        range_m=200, sigma_pos_per_meter=0.0, sigma_pos_floor_m=0.0,
        sigma_quat=0.0, label="test_zero_noise",
    )
    true_pos = np.array([1.0, 2.0, 3.0])
    true_q = np.array([0.0, 0.0, 0.0, 1.0])
    p, q = measure_pose(true_pos, true_q, spec, rng)
    assert np.allclose(p, true_pos)


def test_measure_pose_noise_grows_with_range():
    rng = np.random.default_rng(0)
    n_samples = 1000
    near = np.array([1.0, 0., 0.])      # 1 m range
    far = np.array([100.0, 0., 0.])     # 100 m range
    quat = np.array([0., 0., 0., 1.])
    near_errs = []
    far_errs = []
    for _ in range(n_samples):
        p_near, _ = measure_pose(near, quat, LIDAR_TRIDAR_SHORT, rng)
        p_far, _ = measure_pose(far, quat, LIDAR_TRIDAR_SHORT, rng)
        near_errs.append(np.linalg.norm(p_near - near))
        far_errs.append(np.linalg.norm(p_far - far))
    assert np.mean(far_errs) > np.mean(near_errs)


def test_three_documented_presets_have_distinct_specs():
    assert LIDAR_TRIDAR_SHORT.range_m != LIDAR_RVS_LONG.range_m
    assert LIDAR_RVS_LONG.range_m > LIDAR_TRIDAR_SHORT.range_m
    assert DRAGON_EYE.range_m != LIDAR_TRIDAR_SHORT.range_m
