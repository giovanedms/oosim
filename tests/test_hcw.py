"""Tests for Hill-Clohessy-Wiltshire propagation."""
import numpy as np
from oosim.proxops.hcw import hcw_state_transition_matrix, propagate_hcw, mean_motion


def test_stm_at_zero_is_identity():
    n = 0.001
    Phi = hcw_state_transition_matrix(n, 0.0)
    assert np.allclose(Phi, np.eye(6))


def test_stm_determinant_unity():
    """HCW STM is symplectic; det = 1 for any t."""
    n = 0.0011
    for t in [10.0, 100.0, 600.0, 5400.0]:
        Phi = hcw_state_transition_matrix(n, t)
        assert abs(np.linalg.det(Phi) - 1.0) < 1e-9


def test_propagate_zero_initial_zero_state():
    n = 0.0011
    state = propagate_hcw(np.zeros(6), n, 100.0)
    assert np.allclose(state, np.zeros(6))


def test_along_track_drift():
    """Pure along-track displacement with zero rates: along-track grows linearly
    in time at rate -1.5 * n * x_0 (drift caused by HCW coupling)."""
    n = mean_motion(6378.137 + 400.0)
    state0 = np.array([10.0, 0., 0., 0., 0., 0.])
    state = propagate_hcw(state0, n, 600.0)
    # After 600 s, y should have drifted negatively (V-bar drift)
    assert state[1] < 0.0


def test_iss_mean_motion():
    n = mean_motion(6378.137 + 408.0)
    # ISS orbital period ~92.8 min -> n ~ 0.00113 rad/s
    assert 0.00110 < n < 0.00115
