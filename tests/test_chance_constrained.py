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


def test_qp_chance_constrained_stub_raises():
    with pytest.raises(NotImplementedError):
        qp_chance_constrained_target()
