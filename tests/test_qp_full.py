"""Tests for QP terminal targeting with full (non-spherical) ellipsoid envelope."""
import numpy as np
import pytest

from oosim.proxops.hcw import mean_motion
from oosim.targeting.qp_targeting import qp_terminal_target, HAVE_CVXPY
from oosim.targeting.envelope_specs import CANADARM2_BERTHING


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_qp_with_ellipsoid_envelope():
    """Validate that QP respects an axis-aligned ellipsoid envelope (non-sphere)."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([0.0, -100.0, 0.0, 0.0, 0.0, 0.0])
    target = np.array([0.0, 0.0, 0.0])
    semi = np.array([0.5, 0.5, 0.3])  # ellipsoid semi-axes

    result = qp_terminal_target(
        initial_state=initial, target_pos=target, n=n,
        horizon_steps=20, dt=15.0,
        capture_radius=semi, v_max_terminal=0.05, dv_max_per_step=0.3,
    )
    assert result.success
    # Terminal position should satisfy ellipsoid constraint
    rel = (result.terminal_state[:3] - target) / semi
    assert np.dot(rel, rel) <= 1.001


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_qp_with_canadarm2_preset():
    """End-to-end with the CANADARM2_BERTHING preset (Cygnus/HTV style)."""
    n = mean_motion(6378.137 + 408.0)
    # Chaser starts 30 m behind ISS on V-bar at AI-30 hold point
    initial = np.array([10.0, -30.0, 0.0, 0.0, 0.0, 0.0])
    result = qp_terminal_target(
        initial_state=initial,
        target_pos=CANADARM2_BERTHING.center_pos,
        n=n,
        horizon_steps=15, dt=20.0,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max,
        dv_max_per_step=0.2,
    )
    assert result.success
    rel = (result.terminal_state[:3] - CANADARM2_BERTHING.center_pos) / CANADARM2_BERTHING.pos_semi_axes
    assert np.dot(rel, rel) <= 1.001
    assert np.linalg.norm(result.terminal_state[3:]) <= CANADARM2_BERTHING.vel_max + 1e-3


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_qp_with_vbar_corridor():
    """Solve QP with V-bar corridor enforced over the horizon.

    Convention: chaser approaches from behind on V-bar (y < 0), so the cone
    is parametrized by -y (along-track distance to target) bounding |x| (radial)
    and |z| (cross-track) deviations.
    """
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([3.0, -200.0, 2.0, 0.0, 0.0, 0.0])
    result = qp_terminal_target(
        initial_state=initial,
        target_pos=np.array([0.0, 0.0, 0.0]),
        n=n,
        horizon_steps=25, dt=15.0,
        capture_radius=0.5, v_max_terminal=0.05, dv_max_per_step=0.3,
        enforce_vbar_corridor=True,
    )
    assert result.success
    for k in range(result.states.shape[0]):
        x_k, y_k, z_k = result.states[k, :3]
        assert y_k <= 1e-6, f"V-bar assumption broken at k={k}: y={y_k}"
        assert abs(x_k) <= 0.10 * (-y_k) + 5.0 + 1e-3
        assert abs(z_k) <= 0.05 * (-y_k) + 3.0 + 1e-3
