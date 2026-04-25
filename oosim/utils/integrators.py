"""Numerical integrators used by the proxops module when closed-form HCW STM
is insufficient (perturbed dynamics, sensor noise injection, control loops).

Wraps `scipy.integrate.solve_ivp` with sensible defaults and preserves the
discrete event handling needed for impulsive Δv applications.
"""
from typing import Callable
import numpy as np
from scipy.integrate import solve_ivp


def integrate_with_impulses(rhs: Callable[[float, np.ndarray], np.ndarray],
                            state0: np.ndarray,
                            t_span: tuple[float, float],
                            impulses: list[tuple[float, np.ndarray]] | None = None,
                            n_eval: int = 200,
                            rtol: float = 1e-9,
                            atol: float = 1e-12) -> tuple[np.ndarray, np.ndarray]:
    """Integrate ODE with a sequence of impulsive velocity changes applied in order.

    Args:
        rhs: state derivative function f(t, y) -> dy/dt.
        state0: initial 6-vector (3 pos + 3 vel).
        t_span: (t0, tf) in seconds.
        impulses: list of (t, dv_vec) where dv_vec is added to velocity at time t.
        n_eval: number of evaluation points for output.
        rtol, atol: integrator tolerances.

    Returns:
        (t_array, y_array) where y_array has shape (6, n_eval).
    """
    impulses = sorted(impulses or [], key=lambda p: p[0])
    t_breakpoints = [t_span[0]] + [t for t, _ in impulses] + [t_span[1]]
    t_breakpoints = sorted(set(t_breakpoints))

    times: list[np.ndarray] = []
    states: list[np.ndarray] = []
    state = state0.copy()

    for i in range(len(t_breakpoints) - 1):
        t0, tf = t_breakpoints[i], t_breakpoints[i + 1]
        if tf <= t0:
            continue
        n_local = max(2, int(n_eval * (tf - t0) / (t_span[1] - t_span[0])))
        t_eval = np.linspace(t0, tf, n_local)
        sol = solve_ivp(rhs, (t0, tf), state, t_eval=t_eval,
                        rtol=rtol, atol=atol, method="DOP853")
        times.append(sol.t)
        states.append(sol.y)
        state = sol.y[:, -1].copy()
        # Apply any impulse exactly at tf
        for t_imp, dv in impulses:
            if abs(t_imp - tf) < 1e-9:
                state[3:] += dv

    t_out = np.concatenate(times)
    y_out = np.concatenate(states, axis=1)
    return t_out, y_out
