"""Tests for QP terminal targeting (skipped if cvxpy unavailable)."""
import numpy as np
import pytest

from oosim.proxops.hcw import mean_motion
from oosim.targeting.qp_targeting import qp_terminal_target, HAVE_CVXPY


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_qp_simple_approach():
    """Chaser starting 100 m behind target on V-bar should be steered into a
    small capture sphere around the target with bounded terminal velocity."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([0.0, -100.0, 0.0, 0.0, 0.0, 0.0])
    target = np.array([0.0, 0.0, 0.0])

    result = qp_terminal_target(
        initial_state=initial, target_pos=target, n=n,
        horizon_steps=15, dt=20.0,
        capture_radius=0.5, v_max_terminal=0.05, dv_max_per_step=0.3,
    )
    assert result.success, f"QP failed: {result.solver_status}"
    pos_err = np.linalg.norm(result.terminal_state[:3] - target)
    vel_norm = np.linalg.norm(result.terminal_state[3:])
    assert pos_err <= 0.51  # tolerância numérica
    assert vel_norm <= 0.051
