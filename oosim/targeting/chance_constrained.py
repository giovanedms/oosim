"""Chance-constrained QP terminal targeting (Blackmore-Ono formulation).

Alternative to the soft-terminal-cost approach (`qp_targeting.py` with
`terminal_mode='soft'`). Instead of moving the envelope into the cost,
the chance-constrained formulation enforces it as a probabilistic
constraint:

    Pr( || r_N - r* || <= R ) >= 1 - delta

where delta is the desired risk level (e.g., 0.05 for 95% confidence).

Under Gaussian uncertainty on the propagated state with covariance P_N,
the chance constraint reduces to a deterministic SOC constraint by
inflating the envelope radius by Phi^{-1}(1 - delta) * sqrt(lambda_max(P_N)).

This module is a STUB for the A1 journal extension. The full implementation
requires propagating the UKF posterior covariance through the QP horizon,
which is a non-trivial integration of the estimator and optimizer that
exceeds the IAC paper scope.

References:
    Blackmore, L. & Ono, M. (2009). Convex chance constrained predictive
        control without sampling. AIAA GNC. DOI: 10.2514/6.2009-5876
    Blackmore, L., Ono, M., Williams, B. C. (2011). Chance-Constrained
        Optimal Path Planning With Obstacles. IEEE TRO.
        DOI: 10.1109/tro.2011.2161160
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class ChanceConstraintSpec:
    """Specification for a chance-constrained terminal envelope."""
    nominal_radius_m: float          # nominal workspace radius
    risk_level: float = 0.05         # delta: max acceptable failure prob
    propagated_cov: np.ndarray = None  # 3x3 estimated terminal pos covariance


def inflate_envelope(spec: ChanceConstraintSpec) -> float:
    """Compute the inflated radius that, treated as a hard constraint, gives
    the required chance-constraint guarantee under Gaussian uncertainty.

    For a single chance constraint || r_N - r* || <= R with r_N ~ N(mu, P),
    the equivalent deterministic constraint is

        || mu - r* || <= R - Phi^{-1}(1 - delta) * sqrt(lambda_max(P))

    where Phi is the standard normal CDF. This is the Boole inequality bound
    used in Blackmore-Ono.
    """
    from scipy.stats import norm
    if spec.propagated_cov is None:
        return spec.nominal_radius_m
    eigvals = np.linalg.eigvalsh(spec.propagated_cov)
    lam_max = float(eigvals[-1])
    z = float(norm.ppf(1.0 - spec.risk_level))
    return max(0.0, spec.nominal_radius_m - z * np.sqrt(lam_max))


# Stub for the chance-constrained QP integration. To be developed in F2-F3
# of the A1 journal extension.
def qp_chance_constrained_target(*args, **kwargs):
    """Solve chance-constrained QP terminal targeting.

    NOT IMPLEMENTED. This is the central methodological contribution reserved
    for the A1 journal extension (April 2027). Combines the UKF posterior
    covariance from `oosim.targeting.ukf` with the QP from
    `oosim.targeting.qp_targeting` via the inflated-envelope technique
    above.
    """
    raise NotImplementedError(
        "Chance-constrained QP terminal targeting is reserved for the A1 "
        "journal extension. See `inflate_envelope()` for the helper used in "
        "the deterministic-equivalent reformulation."
    )
