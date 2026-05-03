"""Coupled 13-dimensional state propagator (Module 3 of F2-real).

State vector layout (13 components):
    x[0:3]   r_eci   — position in ECI [km]
    x[3:6]   v_eci   — velocity in ECI [km/s]
    x[6:10]  quat    — body-to-ECI rotation quaternion (scalar-last [qx,qy,qz,qw])
    x[10:13] omega   — body angular velocity [rad/s]

This is the architectural core of the Option C end-to-end pipeline. Translation
and attitude evolve jointly: thrust direction is determined by the body-frame
attitude, so the translational dynamics depend on the attitude state, and the
attitude controller (RCS phase-plane) must run inside the same integrator.

External inputs at each step:
    thrust_body : 3-vector body-frame thrust acceleration [km/s²]
    torque_body : 3-vector body-frame torque [N·m]

Both are provided by upstream controllers (phasing burns + attitude phase-plane).

Reference dynamics (Vallado, Sidi):
    dr/dt = v
    dv/dt = -μ r/|r|³  +  R(q) · thrust_body         (R is body-to-ECI rotation)
    dq/dt = 0.5 · Ω(ω) · q
    dω/dt = I⁻¹ · (torque_body - ω × I·ω)
"""
from dataclasses import dataclass, field
from typing import Callable
import numpy as np
from scipy.integrate import solve_ivp

MU_EARTH = 398600.4418  # km³/s²


def quat_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Body-to-ECI rotation from unit quaternion (scalar-last)."""
    qx, qy, qz, qw = q
    return np.array([
        [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
        [2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qx*qw)],
        [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)],
    ])


def quat_omega_matrix(omega: np.ndarray) -> np.ndarray:
    """Build the Ω(ω) 4x4 matrix for quaternion kinematics dq/dt = 0.5 Ω q.
    Convention: scalar-last quaternion [qx, qy, qz, qw]."""
    wx, wy, wz = omega
    return np.array([
        [0,   wz, -wy, wx],
        [-wz,  0,  wx, wy],
        [wy, -wx,  0,  wz],
        [-wx, -wy, -wz, 0],
    ])


@dataclass
class CoupledStateConfig:
    """Configuration for a coupled 13-dim propagation."""
    inertia: np.ndarray                                          # 3x3 [kg·m²]
    mu: float = MU_EARTH
    thrust_callback: Callable[[float, np.ndarray], np.ndarray] | None = None
    torque_callback: Callable[[float, np.ndarray], np.ndarray] | None = None

    def __post_init__(self):
        self.inertia = np.asarray(self.inertia, dtype=float)
        assert self.inertia.shape == (3, 3)
        self._inertia_inv = np.linalg.inv(self.inertia)

    @property
    def inertia_inv(self):
        return self._inertia_inv


def coupled_dynamics(t: float, x: np.ndarray, cfg: CoupledStateConfig) -> np.ndarray:
    """Right-hand side of the 13-dim coupled ODE."""
    r = x[0:3]
    v = x[3:6]
    q = x[6:10]
    omega = x[10:13]

    # Quaternion may drift from unit norm during integration; normalise locally.
    q = q / np.linalg.norm(q)

    R_body_to_eci = quat_to_rotation_matrix(q)

    # External acceleration/torque from callbacks (default zero)
    a_body = cfg.thrust_callback(t, x) if cfg.thrust_callback is not None else np.zeros(3)
    M_body = cfg.torque_callback(t, x) if cfg.torque_callback is not None else np.zeros(3)

    # Translation
    r_norm = float(np.linalg.norm(r))
    if r_norm < 1e-9:
        a_grav = np.zeros(3)
    else:
        a_grav = -cfg.mu * r / r_norm**3
    a_thrust_eci = R_body_to_eci @ a_body
    dr_dt = v
    dv_dt = a_grav + a_thrust_eci

    # Attitude
    Omega = quat_omega_matrix(omega)
    dq_dt = 0.5 * Omega @ q

    # Euler rotational dynamics
    Iw = cfg.inertia @ omega
    domega_dt = cfg.inertia_inv @ (M_body - np.cross(omega, Iw))

    return np.concatenate([dr_dt, dv_dt, dq_dt, domega_dt])


def propagate_coupled(initial_state: np.ndarray, t_span: tuple[float, float],
                      cfg: CoupledStateConfig, t_eval: np.ndarray | None = None,
                      rtol: float = 1e-9, atol: float = 1e-12,
                      method: str = "DOP853") -> tuple[np.ndarray, np.ndarray]:
    """Propagate the 13-dim coupled state from t_span[0] to t_span[1].

    Args:
        initial_state: 13-vector at t_span[0].
        t_span: (t0, tf) in seconds.
        cfg: CoupledStateConfig with inertia and optional thrust/torque callbacks.
        t_eval: optional array of evaluation times.
        rtol, atol: integrator tolerances.
        method: scipy ODE method.

    Returns:
        (t_array, state_array_shape_13_by_N)
    """
    assert initial_state.shape == (13,), f"expected 13-vector, got {initial_state.shape}"
    sol = solve_ivp(
        fun=lambda t, x: coupled_dynamics(t, x, cfg),
        t_span=t_span, y0=initial_state, t_eval=t_eval,
        rtol=rtol, atol=atol, method=method,
    )
    if not sol.success:
        raise RuntimeError(f"Coupled propagation failed: {sol.message}")
    # Re-normalise quaternion column-wise (DOP853 doesn't enforce constraint)
    for k in range(sol.y.shape[1]):
        q = sol.y[6:10, k]
        sol.y[6:10, k] = q / np.linalg.norm(q)
    return sol.t, sol.y


def make_initial_state(r_eci: np.ndarray, v_eci: np.ndarray,
                        quat: np.ndarray | None = None,
                        omega: np.ndarray | None = None) -> np.ndarray:
    """Pack a 13-dim initial state. Default attitude: identity, zero spin."""
    r = np.asarray(r_eci, dtype=float).flatten()
    v = np.asarray(v_eci, dtype=float).flatten()
    if quat is None:
        quat = np.array([0.0, 0.0, 0.0, 1.0])
    else:
        quat = np.asarray(quat, dtype=float).flatten()
        quat = quat / np.linalg.norm(quat)
    if omega is None:
        omega = np.zeros(3)
    else:
        omega = np.asarray(omega, dtype=float).flatten()
    return np.concatenate([r, v, quat, omega])
