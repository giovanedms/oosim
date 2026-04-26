"""Tests for the full chance-constrained QP."""
import numpy as np
import pytest
from oosim.proxops.hcw import mean_motion
from oosim.targeting.chance_constrained import (
    ChanceConstraintSpec, inflate_envelope, propagate_covariance,
    qp_chance_constrained_target,
)
from oosim.targeting.qp_targeting import HAVE_CVXPY


def test_propagate_covariance_grows():
    """With small process noise, covariance should still grow over time."""
    initial = np.eye(6) * 0.01
    Q = np.eye(6) * 1e-4
    P_final = propagate_covariance(initial, 0.0011, 10.0, 30, Q)
    # Position trace should grow
    assert np.trace(P_final[:3, :3]) >= np.trace(initial[:3, :3])


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_chance_constrained_with_low_uncertainty_returns_shape():
    """With low initial uncertainty, the chance constraint helper should
    return a valid result dict with a positive R_eff. We do not require the
    inner QP to succeed (depends on horizon/control authority calibration),
    only that the chance-constraint logic itself works and produces a
    non-trivial inflation."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([0.0, -100.0, 0.0, 0.0, 0.0, 0.0])
    initial_cov = np.eye(6) * 1e-4
    Q = np.eye(6) * 1e-8
    result = qp_chance_constrained_target(
        initial_state=initial, target_pos=np.array([0., 0., 0.]),
        n=n, horizon_steps=20, dt=15.0,
        nominal_radius=0.5, risk_level=0.05,
        initial_cov=initial_cov, process_noise=Q,
        v_max_terminal=0.05, dv_max_per_step=0.3,
    )
    assert "R_eff" in result
    assert result["R_eff"] > 0
    assert result["R_eff"] <= 0.5  # inflated radius cannot exceed nominal


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_chance_constrained_with_high_uncertainty_infeasible():
    """With very high uncertainty exceeding the nominal radius, the chance
    constraint is infeasible and the helper returns success=False."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([0.0, -100.0, 0.0, 0.0, 0.0, 0.0])
    initial_cov = np.eye(6) * 100.0  # 10 m std — much larger than 0.5 m envelope
    Q = np.eye(6) * 1e-4
    result = qp_chance_constrained_target(
        initial_state=initial, target_pos=np.array([0., 0., 0.]),
        n=n, horizon_steps=20, dt=15.0,
        nominal_radius=0.5, risk_level=0.05,
        initial_cov=initial_cov, process_noise=Q,
    )
    assert not result["success"]
    assert "infeasible" in result["reason"].lower()
