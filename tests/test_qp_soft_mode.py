"""Tests for the soft-terminal QP mode."""
import numpy as np
import pytest
from oosim.proxops.hcw import mean_motion
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target, HAVE_CVXPY


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_soft_mode_handles_far_initial():
    """A moderately-far start where hard mode would be infeasible, soft mode returns OK."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([10.0, -200.0, 0.0, 0.0, 0.0, 0.0])  # 200 m behind
    res_soft = qp_terminal_target(
        initial_state=initial, target_pos=CANADARM2_BERTHING.center_pos, n=n,
        horizon_steps=20, dt=15.0,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max,
        dv_max_per_step=0.3,
        terminal_mode="soft",
    )
    assert res_soft.success


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_soft_mode_invalid_string_raises():
    n = mean_motion(6378.137 + 408.0)
    with pytest.raises(ValueError):
        qp_terminal_target(
            initial_state=np.zeros(6), target_pos=np.zeros(3), n=n,
            horizon_steps=5, dt=10.0, terminal_mode="invalid",
        )


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_hard_and_soft_match_when_constraint_inactive():
    """When the chaser is already inside the envelope, hard and soft modes should
    produce nearly the same control sequence (both essentially do nothing)."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([10.0, 0.05, 0.05, 0.0, 0.0, 0.0])  # already near target
    target = CANADARM2_BERTHING.center_pos
    res_hard = qp_terminal_target(
        initial_state=initial, target_pos=target, n=n,
        horizon_steps=10, dt=10.0,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max, dv_max_per_step=0.05,
        terminal_mode="hard",
    )
    res_soft = qp_terminal_target(
        initial_state=initial, target_pos=target, n=n,
        horizon_steps=10, dt=10.0,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max, dv_max_per_step=0.05,
        terminal_mode="soft",
    )
    assert res_hard.success and res_soft.success
    # Costs differ (soft has terminal penalty) but both terminate near target
    assert np.linalg.norm(res_hard.terminal_state[:3] - target) < 0.5
    assert np.linalg.norm(res_soft.terminal_state[:3] - target) < 0.5
