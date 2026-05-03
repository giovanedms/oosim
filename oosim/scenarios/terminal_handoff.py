"""Terminal-phase MPC handoff to coupled-state propagator (Module 6 of F2-real).

Connects M5 PhasingPlan output to M3 coupled 13-dim propagator (translation +
attitude) via a stateful TerminalMPCController whose thrust_callback solves the
existing qp_terminal_target QP at fixed periods and applies its first impulse
as a finite-duration body-frame thrust.

Pipeline:
  1. Initialise chaser 13-dim state from M5 plan (final ECI + initial quat/omega).
  2. Pre-compute target ECI trajectory (Kepler+J2) over the terminal window.
  3. Build TerminalMPCController with target_eci_callback that interpolates step 2.
  4. Inject controller.thrust_callback into CoupledStateConfig.
  5. Call propagate_coupled to integrate the terminal phase.
  6. Compute terminal LVLH state at handoff_end and return TerminalSimResult.

Frame-conversion notes:
  - QP works in meters and m/s (capture_radius=0.3 m, v_max=0.05 m/s).
  - LVLH dv from QP is rotated to ECI via R_eci_to_lvlh.T (orthogonal rotation
    only — Coriolis correction is applied per-state in eci_state_to_lvlh_relative,
    not per-impulse).
  - ECI dv is converted to body-frame thrust via R_body_to_eci.T evaluated at
    the chaser quaternion at the moment of replan.
"""
from dataclasses import dataclass
from typing import Callable
import numpy as np

from oosim.proxops.coupled_state import (
    CoupledStateConfig, propagate_coupled, quat_to_rotation_matrix, MU_EARTH
)
from oosim.proxops.eci_propagator import propagate_orbit
from oosim.utils.frames_dynamic import eci_state_to_lvlh_relative
from oosim.utils.frames import eci_to_lvlh_rotation
from oosim.targeting.qp_targeting import qp_terminal_target


@dataclass
class TerminalMPCConfig:
    """Config for the terminal-phase MPC controller."""
    target_pos_lvlh: np.ndarray              # capture envelope centre [m, LVLH]
    target_n: float                          # target mean motion [rad/s]
    capture_radius: float = 0.3              # [m]
    v_max_terminal: float = 0.05             # [m/s]
    qp_dt: float = 30.0                      # control replan period [s]
    qp_horizon_steps: int = 20
    qp_dv_max_per_step: float = 0.5          # [m/s]
    thrust_acceleration: float = 5.6e-5      # body-frame max accel [km/s^2]
    terminal_mode: str = 'soft'              # 'soft' or 'hard'
    qp_solver: str = 'ECOS'                  # CVXPY solver; 'SCS' more robust for edge states


@dataclass
class ImpulseLogEntry:
    t: float
    dv_lvlh_m_s: np.ndarray            # 3-vector LVLH Δv from QP [m/s]
    dv_eci_km_s: np.ndarray            # 3-vector ECI Δv (rotated) [km/s]
    duration_s: float
    qp_status: str


@dataclass
class TerminalSimResult:
    t_array: np.ndarray                # times [s]
    coupled_states: np.ndarray         # shape (13, N)
    target_eci_states: np.ndarray      # shape (6, N) — propagated target
    impulse_log: list                  # list of ImpulseLogEntry
    terminal_lvlh: dict                # final LVLH relative state {'dr_lvlh','dv_lvlh'}
    terminal_distance_m: float         # final ||dr_lvlh|| in metres


class TerminalMPCController:
    """Stateful MPC injected into coupled-state RHS via thrust_callback.

    State machine:
      - if t >= next_qp_time AND t >= burn_until: replan (call _replan)
      - if t < burn_until: return self.current_thrust_body
      - else: return zeros(3)

    target_eci_callback: float -> np.ndarray(6,) — must return ECI state of
    target at time t. Typically built by interpolating a pre-propagated array.
    """

    def __init__(self, cfg: TerminalMPCConfig,
                 target_eci_callback: Callable[[float], np.ndarray]):
        self.cfg = cfg
        self.target_eci_callback = target_eci_callback
        self.next_qp_time: float = 0.0
        self.burn_until: float = -1.0
        self.current_thrust_body: np.ndarray = np.zeros(3)
        self.impulse_log: list = []

    def thrust_callback(self, t: float, x: np.ndarray) -> np.ndarray:
        if t >= self.next_qp_time and t >= self.burn_until:
            self._replan(t, x)
        if t < self.burn_until:
            return self.current_thrust_body
        return np.zeros(3)

    def _replan(self, t: float, x: np.ndarray) -> None:
        target_state = self.target_eci_callback(t)
        # LVLH relative state in km, km/s
        rel = eci_state_to_lvlh_relative(
            x[0:3], x[3:6], target_state[:3], target_state[3:6], mu=MU_EARTH
        )
        # QP works in m, m/s
        rel_m = np.empty(6)
        rel_m[0:3] = rel[0:3] * 1000.0
        rel_m[3:6] = rel[3:6] * 1000.0
        result = qp_terminal_target(
            initial_state=rel_m,
            target_pos=np.asarray(self.cfg.target_pos_lvlh, dtype=float),
            n=self.cfg.target_n,
            horizon_steps=self.cfg.qp_horizon_steps,
            dt=self.cfg.qp_dt,
            capture_radius=self.cfg.capture_radius,
            v_max_terminal=self.cfg.v_max_terminal,
            dv_max_per_step=self.cfg.qp_dv_max_per_step,
            terminal_mode=self.cfg.terminal_mode,
            solver=self.cfg.qp_solver,
        )
        if not result.success:
            self.current_thrust_body = np.zeros(3)
            self.burn_until = t  # no burn this period
            self.next_qp_time = t + self.cfg.qp_dt
            self.impulse_log.append(ImpulseLogEntry(
                t=t, dv_lvlh_m_s=np.zeros(3), dv_eci_km_s=np.zeros(3),
                duration_s=0.0, qp_status=result.solver_status,
            ))
            return
        dv_lvlh_m_s = result.delta_vs[0]
        dv_lvlh_km_s = dv_lvlh_m_s / 1000.0
        # ECI <- LVLH rotation: R_eci_to_lvlh maps ECI vec -> LVLH vec, so
        # to convert dv_lvlh (LVLH) back to ECI we use its transpose.
        R_eci_to_lvlh = eci_to_lvlh_rotation(target_state[:3], target_state[3:6])
        dv_eci_km_s = R_eci_to_lvlh.T @ dv_lvlh_km_s
        dv_mag = float(np.linalg.norm(dv_eci_km_s))
        if dv_mag < 1e-12:
            self.current_thrust_body = np.zeros(3)
            self.burn_until = t
            self.next_qp_time = t + self.cfg.qp_dt
            self.impulse_log.append(ImpulseLogEntry(
                t=t, dv_lvlh_m_s=dv_lvlh_m_s.copy(), dv_eci_km_s=dv_eci_km_s.copy(),
                duration_s=0.0, qp_status=result.solver_status,
            ))
            return
        burn_dur = dv_mag / self.cfg.thrust_acceleration
        thrust_eci_unit = dv_eci_km_s / dv_mag
        # Convert ECI thrust direction to body frame: a_body = R_body_to_eci^T @ a_eci
        R_body_to_eci = quat_to_rotation_matrix(x[6:10] / np.linalg.norm(x[6:10]))
        thrust_body_unit = R_body_to_eci.T @ thrust_eci_unit
        self.current_thrust_body = thrust_body_unit * self.cfg.thrust_acceleration
        self.burn_until = t + burn_dur
        # Don't replan during burn; replan immediately after burn ends
        self.next_qp_time = max(t + burn_dur, t + self.cfg.qp_dt)
        self.impulse_log.append(ImpulseLogEntry(
            t=t, dv_lvlh_m_s=dv_lvlh_m_s.copy(), dv_eci_km_s=dv_eci_km_s.copy(),
            duration_s=burn_dur, qp_status=result.solver_status,
        ))


def _build_target_callback(target_initial_eci: np.ndarray, t_max: float,
                            n_points: int = 200, use_j2: bool = True):
    """Pre-propagate target and return a linear-interpolation callback."""
    t_array = np.linspace(0.0, t_max, n_points)
    states = propagate_orbit(target_initial_eci, t_array,
                             mu=MU_EARTH, include_j2=use_j2)  # (N, 6)
    def cb(t):
        # Linear interpolation per component
        return np.array([np.interp(t, t_array, states[:, i]) for i in range(6)])
    return cb, t_array, states


def simulate_terminal_phase(
    chaser_initial_eci: np.ndarray,           # (6,) ECI [km, km/s]
    target_initial_eci: np.ndarray,           # (6,) ECI [km, km/s]
    initial_quat: np.ndarray,                 # (4,) [qx,qy,qz,qw]
    initial_omega: np.ndarray,                # (3,) [rad/s]
    inertia: np.ndarray,                      # (3,3) [kg m^2]
    mpc_cfg: TerminalMPCConfig,
    t_terminal: float = 600.0,                # [s]
    *,
    n_eval_points: int = 300,
    integrator_rtol: float = 1e-8,
    use_j2_for_target: bool = True,
) -> TerminalSimResult:
    """Run terminal-phase coupled-state simulation with MPC controller."""
    target_cb, t_target, target_states = _build_target_callback(
        target_initial_eci, t_max=t_terminal,
        n_points=n_eval_points, use_j2=use_j2_for_target,
    )
    controller = TerminalMPCController(mpc_cfg, target_cb)
    cfg_coupled = CoupledStateConfig(
        inertia=inertia,
        thrust_callback=controller.thrust_callback,
    )
    initial_state_13 = np.concatenate([
        chaser_initial_eci[:3], chaser_initial_eci[3:6],
        np.asarray(initial_quat, dtype=float) /
            float(np.linalg.norm(initial_quat)),
        np.asarray(initial_omega, dtype=float),
    ])
    t_eval = np.linspace(0.0, t_terminal, n_eval_points)
    t_out, x_out = propagate_coupled(
        initial_state_13, (0.0, t_terminal), cfg_coupled,
        t_eval=t_eval, rtol=integrator_rtol, atol=1e-11,
    )
    # Re-build target trajectory aligned to t_out
    target_states_out = np.zeros((6, len(t_out)))
    for i, t in enumerate(t_out):
        target_states_out[:, i] = target_cb(float(t))
    # Terminal LVLH
    rel_term = eci_state_to_lvlh_relative(
        x_out[0:3, -1], x_out[3:6, -1],
        target_states_out[:3, -1], target_states_out[3:6, -1],
        mu=MU_EARTH,
    )
    terminal_lvlh = {'dr_lvlh': rel_term[:3], 'dv_lvlh': rel_term[3:6]}
    terminal_distance_m = float(np.linalg.norm(rel_term[:3]) * 1000.0)
    return TerminalSimResult(
        t_array=t_out, coupled_states=x_out,
        target_eci_states=target_states_out,
        impulse_log=controller.impulse_log,
        terminal_lvlh=terminal_lvlh,
        terminal_distance_m=terminal_distance_m,
    )
