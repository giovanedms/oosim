"""Tests for the UKF state estimator."""
import numpy as np
from oosim.proxops.hcw import mean_motion, propagate_hcw
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


def test_predict_step_zero_process_noise_matches_hcw():
    """With zero process noise, UKF predict should match the HCW STM exactly."""
    n = mean_motion(6378.137 + 408.0)
    initial_mean = np.array([100.0, -200.0, 50.0, 0.0, 0.0, 0.0])
    initial_cov = np.eye(6) * 1e-6  # tight initial covariance
    state = UKFState(mean=initial_mean, cov=initial_cov)
    Q = np.zeros((6, 6))
    state_pred = ukf_predict(state, n, dt=60.0, process_noise_cov=Q)

    # Reference propagation
    ref = propagate_hcw(initial_mean, n, 60.0)
    assert np.allclose(state_pred.mean, ref, atol=1e-4)


def test_update_reduces_covariance():
    """A measurement update with finite noise should reduce trace of position cov."""
    n = mean_motion(6378.137 + 408.0)
    initial_mean = np.array([100.0, -200.0, 0.0, 0.0, 0.0, 0.0])
    initial_cov = np.eye(6)
    initial_cov[:3, :3] *= 1.0  # 1 m^2 position uncertainty
    initial_cov[3:, 3:] *= 1e-4  # 0.01 m/s velocity uncertainty
    state = UKFState(mean=initial_mean, cov=initial_cov)

    measurement = np.array([100.05, -199.9, 0.02])  # noisy measurement near truth
    R = np.eye(3) * 0.01  # 0.1 m std measurement noise
    state_post = ukf_update(state, measurement, R)

    pos_cov_trace_before = np.trace(state.cov[:3, :3])
    pos_cov_trace_after = np.trace(state_post.cov[:3, :3])
    assert pos_cov_trace_after < pos_cov_trace_before


def test_predict_update_filter_cycle_converges_to_truth():
    """Run a 30-step filter on noisy synthetic data — mean should track truth."""
    rng = np.random.default_rng(42)
    n = mean_motion(6378.137 + 408.0)
    dt = 5.0
    truth = np.array([100.0, -300.0, 0.0, 0.0, 0.0, 0.0])

    state = UKFState(mean=truth + rng.normal(0, 5, 6),
                     cov=np.eye(6) * 25.0)
    Q = np.eye(6) * 1e-6
    R = np.eye(3) * 0.04

    for _ in range(30):
        state = ukf_predict(state, n, dt, Q)
        truth = propagate_hcw(truth, n, dt)
        meas = truth[:3] + rng.normal(0, 0.2, 3)
        state = ukf_update(state, meas, R)

    err = np.linalg.norm(state.mean[:3] - truth[:3])
    assert err < 1.0  # tracks position to within 1 m after 30 steps
