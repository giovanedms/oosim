"""Online QP-based berthing-compatible terminal targeting.

Formulation (contribution I3 of the IAC paper):

    minimize    || Δv ||^2  +  lambda_pos * || r_f - r_target ||^2
    subject to  HCW discretized dynamics (linear)
                workspace ellipsoid                  (quadratic, SOC)
                V-bar corridor over horizon          (linear)
                || v_f || <= v_max                   (SOC)
                || Δv_k || <= dv_max per step        (SOC, RCS duty-cycle proxy)

Solved with CVXPY + ECOS interior-point.

References:
    Açıkmeşe, B. & Blackmore, L. (2011). Lossless Convexification. ACC.
        DOI: 10.1109/ACC.2011.5990959
    Szmuk, Reynolds, Açıkmeşe (2020). Successive Convexification for Real-Time 6DOF.
        JGCD. DOI: 10.2514/1.G004549
    Echigo et al. (2023). Convex Trajectory Planning for Proximity Operations.
        AIAA SciTech. DOI: 10.2514/6.2023-0493

This is the v0 functional implementation; full SOC workspace constraint with
non-axis-aligned ellipsoid will be added in F2 after capture-envelope review
with co-authors.
"""
from dataclasses import dataclass
import numpy as np

try:
    import cvxpy as cp
    HAVE_CVXPY = True
except ImportError:
    HAVE_CVXPY = False

from ..proxops.hcw import hcw_state_transition_matrix


@dataclass
class QPTargetingResult:
    """Result of one QP solve."""
    success: bool
    delta_vs: np.ndarray              # (N, 3) impulse sequence in m/s
    states: np.ndarray                # (N+1, 6) state trajectory in LVLH
    terminal_state: np.ndarray        # 6-vector at horizon end
    cost: float
    solver_status: str


def _hcw_discretize(n: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (A, B) discrete-time matrices for HCW with impulsive Δv input.

    State: [x, y, z, vx, vy, vz] in LVLH.
    Input: impulsive Δv applied at start of step.
    A = Phi(dt), B = Phi(dt) @ [0; I_3] propagates Δv-induced state at next step.
    """
    Phi = hcw_state_transition_matrix(n, dt)
    A = Phi
    B_impulse = np.vstack([np.zeros((3, 3)), np.eye(3)])  # Δv enters velocity slot
    B = Phi @ B_impulse
    return A, B


def qp_terminal_target(initial_state: np.ndarray,
                       target_pos: np.ndarray,
                       n: float,
                       horizon_steps: int = 20,
                       dt: float = 30.0,
                       capture_radius: float | np.ndarray = 0.3,
                       v_max_terminal: float = 0.05,
                       dv_max_per_step: float = 0.5,
                       lambda_pos: float = 1.0,
                       enforce_vbar_corridor: bool = False,
                       vbar_slope_y: float = 0.10, vbar_intercept_y: float = 5.0,
                       vbar_slope_z: float = 0.05, vbar_intercept_z: float = 3.0,
                       solver: str = "ECOS") -> QPTargetingResult:
    """Solve QP for berthing-compatible terminal state.

    Args:
        initial_state: 6-vector LVLH [x, y, z, vx, vy, vz] at t=0.
        target_pos: 3-vector LVLH target position (capture envelope center).
        n: target orbit mean motion [rad/s].
        horizon_steps: number of discrete control steps.
        dt: timestep [s].
        capture_radius: scalar (sphere) or 3-vector (axis-aligned ellipsoid
            semi-axes) for the workspace constraint at terminal time [m].
        v_max_terminal: max ||v|| at horizon end [m/s].
        dv_max_per_step: max ||Δv|| per impulse [m/s].
        lambda_pos: weight on terminal position error.
        enforce_vbar_corridor: if True, enforce |y_k| <= sy*|x_k|+by and
            |z_k| <= sz*|x_k|+bz over the entire horizon (V-bar approach).
        vbar_slope_y, vbar_intercept_y: V-bar lateral cone parameters.
        vbar_slope_z, vbar_intercept_z: V-bar vertical cone parameters.
        solver: CVXPY solver name.

    Returns:
        QPTargetingResult.
    """
    if not HAVE_CVXPY:
        raise RuntimeError("cvxpy is required. pip install cvxpy ecos")

    A, B = _hcw_discretize(n, dt)
    nx, nu = 6, 3
    N = horizon_steps

    x = cp.Variable((N + 1, nx))
    u = cp.Variable((N, nu))  # Δv per step in m/s

    cons = [x[0] == initial_state]
    for k in range(N):
        cons.append(x[k + 1] == A @ x[k] + B @ u[k])
        cons.append(cp.norm(u[k], 2) <= dv_max_per_step)
        if enforce_vbar_corridor:
            # V-bar corridor (one-sided assumption: chaser approaches from behind,
            # so y_k <= 0 throughout the horizon; |y_k| = -y_k is affine, which
            # makes the cone constraint DCP-compliant). For bilateral V-bar
            # excursions the user must run two passes (positive- and
            # negative-y branches) and pick the better solution.
            cons.append(x[k, 1] <= 0.0)  # explicit assumption
            cons.append(cp.abs(x[k, 0]) <= -vbar_slope_y * x[k, 1] + vbar_intercept_y)  # radial vs along-track distance
            cons.append(cp.abs(x[k, 2]) <= -vbar_slope_z * x[k, 1] + vbar_intercept_z)  # cross-track vs along-track

    # Terminal capture envelope: scalar -> sphere, 3-vector -> axis-aligned ellipsoid
    if np.isscalar(capture_radius):
        cons.append(cp.norm(x[N, :3] - target_pos, 2) <= float(capture_radius))
    else:
        semi = np.asarray(capture_radius, dtype=float)
        # Ellipsoid: ((r - r*) / semi)^T ((r - r*) / semi) <= 1
        cons.append(cp.norm(cp.multiply(1.0 / semi, x[N, :3] - target_pos), 2) <= 1.0)

    # Terminal velocity bound
    cons.append(cp.norm(x[N, 3:], 2) <= v_max_terminal)

    # Cost
    cost = cp.sum_squares(u) + lambda_pos * cp.sum_squares(x[N, :3] - target_pos)

    problem = cp.Problem(cp.Minimize(cost), cons)
    problem.solve(solver=solver)

    if problem.status not in ("optimal", "optimal_inaccurate"):
        return QPTargetingResult(
            success=False, delta_vs=np.zeros((N, nu)),
            states=np.zeros((N + 1, nx)), terminal_state=np.zeros(nx),
            cost=np.inf, solver_status=problem.status,
        )

    return QPTargetingResult(
        success=True,
        delta_vs=u.value,
        states=x.value,
        terminal_state=x.value[-1],
        cost=float(problem.value),
        solver_status=problem.status,
    )
