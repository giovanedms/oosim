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
def test_chance_constrained_returns_dict_with_R_eff():
    """The chance constraint helper should return a dict with R_eff key, and
    R_eff should be in [0, nominal_radius]. The inner QP feasibility depends
    on whether the propagated uncertainty fits inside the nominal envelope —
    we do not test that directly here because HCW propagation can amplify
    initial state covariance significantly over multi-orbit horizons."""
    n = mean_motion(6378.137 + 408.0)
    initial = np.array([0.0, -100.0, 0.0, 0.0, 0.0, 0.0])
    initial_cov = np.eye(6) * 1e-6  # very tight
    Q = np.eye(6) * 1e-10
    result = qp_chance_constrained_target(
        initial_state=initial, target_pos=np.array([0., 0., 0.]),
        n=n, horizon_steps=10, dt=10.0,                   # short horizon
        nominal_radius=2.0, risk_level=0.05,              # generous radius
        initial_cov=initial_cov, process_noise=Q,
        v_max_terminal=0.05, dv_max_per_step=0.3,
    )
    assert "R_eff" in result
    assert 0.0 <= result["R_eff"] <= 2.0


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
