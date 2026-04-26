"""Tests for chance-constrained envelope inflation."""
import numpy as np
import pytest
from oosim.targeting.chance_constrained import (
    ChanceConstraintSpec, inflate_envelope, qp_chance_constrained_target,
)


def test_inflate_envelope_no_cov_returns_nominal():
    spec = ChanceConstraintSpec(nominal_radius_m=0.5, risk_level=0.05)
    assert inflate_envelope(spec) == 0.5


def test_inflate_envelope_with_cov_shrinks_admissible_set():
    """Higher uncertainty should reduce the deterministic-equivalent radius."""
    P = np.eye(3) * 0.01  # 1 cm 1-sigma per axis
    spec = ChanceConstraintSpec(nominal_radius_m=0.5, risk_level=0.05, propagated_cov=P)
    inflated = inflate_envelope(spec)
    # Phi^{-1}(0.95) ~ 1.645; sqrt(lambda_max) = 0.1; so inflated = 0.5 - 1.645*0.1 = 0.336
    assert 0.30 < inflated < 0.40


def test_qp_chance_constrained_now_implemented():
    """qp_chance_constrained_target was a stub raising NotImplementedError;
    after the F1+++++++++++ implementation it is callable. We just check it's
    no longer raising NotImplementedError on call."""
    # API shape — should not raise NotImplementedError
    import numpy as np
    from oosim.proxops.hcw import mean_motion
    n = mean_motion(6378.137 + 408.0)
    try:
        qp_chance_constrained_target(
            initial_state=np.array([0., -100., 0., 0., 0., 0.]),
            target_pos=np.array([0., 0., 0.]), n=n,
            horizon_steps=10, dt=15.0,
            nominal_radius=0.5, risk_level=0.05,
        )
    except NotImplementedError:
        pytest.fail("qp_chance_constrained_target should be implemented now")
