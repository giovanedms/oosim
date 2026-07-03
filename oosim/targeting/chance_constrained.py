"""Chance-constrained QP terminal targeting (Blackmore-Ono formulation).

Full implementation: instead of moving the envelope into the cost as a soft
penalty (which sacrifices the safety guarantee), enforce it as a probabilistic
constraint reduced to its deterministic equivalent under Gaussian uncertainty:

    Pr( || r_N - r* || <= R ) >= 1 - delta

becomes the deterministic SOC constraint

    || r_N_mean - r* || <= R - Phi^{-1}(1-delta) * sqrt(lambda_max(P_N))

where P_N is the predicted terminal-state covariance from the UKF.

This restores the formal safety guarantee that the soft-cost formulation
sacrifices, at the cost of an inflated envelope that depends on the
posterior uncertainty.

References:
    Blackmore, L. & Ono, M. (2009). Convex chance constrained predictive
        control without sampling. AIAA GNC. DOI: 10.2514/6.2009-5876
    Blackmore, L., Ono, M., Williams, B. C. (2011). Chance-Constrained
        Optimal Path Planning With Obstacles. IEEE TRO.
        DOI: 10.1109/tro.2011.2161160
"""
from dataclasses import dataclass
import numpy as np

try:
    import cvxpy as cp  # noqa: F401  # availability probe only; QP solve delegated to qp_targeting
    HAVE_CVXPY = True
except ImportError:
    HAVE_CVXPY = False

from ..proxops.hcw import hcw_state_transition_matrix


@dataclass
class ChanceConstraintSpec:
    """Specification for a chance-constrained terminal envelope."""
    nominal_radius_m: float                    # nominal workspace radius
    risk_level: float = 0.05                    # delta: max acceptable failure prob
    propagated_cov: np.ndarray = None           # 3x3 estimated terminal pos covariance


def inflate_envelope(spec: ChanceConstraintSpec) -> float:
    """Compute the inflated radius giving the chance-constraint guarantee."""
    from scipy.stats import norm
    if spec.propagated_cov is None:
        return spec.nominal_radius_m
    eigvals = np.linalg.eigvalsh(spec.propagated_cov)
    lam_max = float(eigvals[-1])
    z = float(norm.ppf(1.0 - spec.risk_level))
    return max(0.0, spec.nominal_radius_m - z * np.sqrt(lam_max))


def propagate_covariance(initial_cov: np.ndarray, n: float, dt: float,
                          steps: int, process_noise: np.ndarray) -> np.ndarray:
    """Propagate state covariance forward through HCW dynamics.

    P_{k+1} = Phi P_k Phi^T + Q

    Returns the 6x6 covariance at step `steps`.
    """
    Phi = hcw_state_transition_matrix(n, dt)
    P = initial_cov.copy()
    for _ in range(steps):
        P = Phi @ P @ Phi.T + process_noise
    return P


def qp_chance_constrained_target(initial_state: np.ndarray,
                                   target_pos: np.ndarray,
                                   n: float,
                                   horizon_steps: int = 20,
                                   dt: float = 30.0,
                                   nominal_radius: float = 0.3,
                                   risk_level: float = 0.05,
                                   initial_cov: np.ndarray = None,
                                   process_noise: np.ndarray = None,
                                   v_max_terminal: float = 0.05,
                                   dv_max_per_step: float = 0.5,
                                   solver: str = "ECOS"):
    """Solve QP with chance-constrained terminal envelope.

    Same architecture as `qp_terminal_target` (hard mode) but the radius is
    inflated according to the predicted terminal-state covariance.

    Args:
        initial_state: 6-vector LVLH [x, y, z, vx, vy, vz].
        target_pos: 3-vector target.
        n: target orbit mean motion [rad/s].
        horizon_steps, dt, nominal_radius, v_max_terminal, dv_max_per_step:
            same as `qp_terminal_target`.
        risk_level: max acceptable Pr(envelope-violation), e.g. 0.05.
        initial_cov: 6x6 initial state covariance estimate. If None, defaults
            to 1 m std position / 1 cm/s std velocity (typical post-UKF).
        process_noise: 6x6 process noise covariance per step. Defaults to
            very small (1e-6 I) — appropriate when HCW is high-fidelity.

    Returns:
        Same as `qp_terminal_target`.
    """
    if not HAVE_CVXPY:
        raise RuntimeError("cvxpy is required. pip install cvxpy ecos")
    if initial_cov is None:
        initial_cov = np.diag([1.0, 1.0, 1.0, 1e-4, 1e-4, 1e-4])
    if process_noise is None:
        process_noise = np.eye(6) * 1e-6

    P_N = propagate_covariance(initial_cov, n, dt, horizon_steps, process_noise)
    spec = ChanceConstraintSpec(
        nominal_radius_m=nominal_radius,
        risk_level=risk_level,
        propagated_cov=P_N[:3, :3],
    )
    R_eff = inflate_envelope(spec)

    # If the inflated radius is non-positive, the chance constraint is
    # infeasible — cannot satisfy the desired risk level given uncertainty.
    if R_eff <= 0.0:
        return {"success": False, "R_eff": R_eff,
                "reason": "chance constraint infeasible — uncertainty exceeds nominal envelope"}

    # Now solve the standard hard-constraint QP with the inflated radius
    from .qp_targeting import qp_terminal_target
    result = qp_terminal_target(
        initial_state=initial_state, target_pos=target_pos, n=n,
        horizon_steps=horizon_steps, dt=dt,
        capture_radius=R_eff,
        v_max_terminal=v_max_terminal,
        dv_max_per_step=dv_max_per_step,
        terminal_mode="hard", solver=solver,
    )
    # Attach the inflation diagnostic
    return {"success": result.success, "R_eff": R_eff, "R_nominal": nominal_radius,
            "qp_result": result}
