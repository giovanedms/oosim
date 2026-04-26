"""Tests for the non-cooperative tumbling target UKF."""
import numpy as np
from oosim.targeting.uncooperative import (
    TumblingState, tumbling_predict, tumbling_update_pose_and_rate,
    predict_capture_window,
)


def test_predict_with_zero_omega_preserves_attitude():
    state = TumblingState(
        mean=np.array([10.0, 0., 0., 0., 0., 0., 0., 0., 0.]),
        cov=np.eye(9) * 0.01,
    )
    Q = np.zeros((9, 9))
    new_state = tumbling_predict(state, n_motion=0.0011, dt=10.0, process_noise_cov=Q)
    # omega remains zero
    assert np.allclose(new_state.mean[6:9], 0.0, atol=1e-9)


def test_update_with_consistent_measurement_reduces_uncertainty():
    state = TumblingState(
        mean=np.array([10.0, 0., 0., 0., 0., 0., 0.05, 0., 0.]),
        cov=np.eye(9) * 1.0,
    )
    R = np.eye(6) * 0.001
    new_state = tumbling_update_pose_and_rate(
        state,
        pos_meas=np.array([10.0, 0., 0.]),
        omega_meas=np.array([0.05, 0., 0.]),
        measurement_noise_cov=R,
    )
    # Trace of covariance reduced
    assert np.trace(new_state.cov) < np.trace(state.cov)


def test_predict_capture_window_returns_evolving_pose():
    state = TumblingState(
        # spin around y-axis so x-axis grasping fixture rotates
        mean=np.array([10.0, 0., 0., 0., 0., 0., 0., 0.1, 0.]),
        cov=np.eye(9) * 0.01,
    )
    grasping_body = np.array([0.5, 0., 0.])  # along x-axis in body frame
    out = predict_capture_window(state, horizon_s=30.0, grasping_geometry_target_body=grasping_body)
    assert "times" in out and "poses_lvlh" in out
    assert out["poses_lvlh"].shape == (30, 3)
    # Pose should evolve over 30 s of 0.1 rad/s rotation = 3 rad ≈ 172 deg
    assert not np.allclose(out["poses_lvlh"][0], out["poses_lvlh"][-1], atol=1e-3)
