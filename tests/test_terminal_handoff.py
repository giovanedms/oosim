"""Tests for M6 terminal-phase MPC handoff."""
import numpy as np
import pytest
from oosim.scenarios.terminal_handoff import (
    TerminalMPCConfig, simulate_terminal_phase, TerminalSimResult,
)
from oosim.proxops.coupled_state import MU_EARTH

INERTIA_SOYUZ = np.diag([3850.0, 3920.0, 1240.0])
R_E = 6378.137


def make_iss_circular(altitude_km=420.0, true_anomaly_deg=0.0):
    a = R_E + altitude_km
    v = np.sqrt(MU_EARTH / a)
    th = np.radians(true_anomaly_deg)
    r = a * np.array([np.cos(th), np.sin(th), 0.0])
    vv = v * np.array([-np.sin(th), np.cos(th), 0.0])
    return np.concatenate([r, vv])


def make_chaser_offset_lvlh(target_state, dr_lvlh_km, dv_lvlh_km_s=None):
    """Build a chaser ECI state offset from target by a known LVLH delta."""
    from oosim.utils.frames_dynamic import lvlh_relative_to_eci_state
    if dv_lvlh_km_s is None:
        dv_lvlh_km_s = np.zeros(3)
    rel = np.concatenate([dr_lvlh_km, dv_lvlh_km_s])
    r_chaser, v_chaser = lvlh_relative_to_eci_state(
        rel, target_state[:3], target_state[3:6], mu=MU_EARTH,
    )
    return np.concatenate([r_chaser, v_chaser])


def default_mpc_cfg(target_state):
    a = float(np.linalg.norm(target_state[:3]))
    n = float(np.sqrt(MU_EARTH / a**3))
    # qp_dt=150s keeps replan frequency low enough that the effect of each
    # impulse is visible before the next replan, preventing velocity accumulation
    # across receding-horizon iterations.  h=3 gives a 450 s planning horizon
    # covering the full 400 s terminal window.
    return TerminalMPCConfig(
        target_pos_lvlh=np.array([0.0, -10.0, 0.0]),  # 10 m behind target on V-bar
        target_n=n,
        qp_dt=150.0,
        qp_horizon_steps=3,
        qp_dv_max_per_step=0.3,
    )


def test_terminal_phase_returns_sim_result_with_decreasing_distance():
    """Chaser starting 50 m away on V-bar should approach the envelope.

    use_j2_for_target=False ensures the target callback uses the same two-body
    gravity model as the coupled-state integrator; J2 secular drift would
    otherwise cause a fictitious ECI divergence over 400 s that is unrelated to
    the MPC performance under test.
    """
    target = make_iss_circular()
    # Chaser 50 m behind on V-bar (LVLH y < 0), zero relative velocity
    chaser = make_chaser_offset_lvlh(
        target, dr_lvlh_km=np.array([0.0, -50.0e-3, 0.0]),
    )
    cfg = default_mpc_cfg(target)
    res = simulate_terminal_phase(
        chaser_initial_eci=chaser, target_initial_eci=target,
        initial_quat=np.array([0., 0., 0., 1.]), initial_omega=np.zeros(3),
        inertia=INERTIA_SOYUZ, mpc_cfg=cfg, t_terminal=400.0,
        n_eval_points=200, use_j2_for_target=False,
    )
    assert isinstance(res, TerminalSimResult)
    initial_dist = 50.0  # m
    final_dist = res.terminal_distance_m
    assert final_dist < initial_dist, \
        f"chaser should approach: initial=50 m, final={final_dist:.2f} m"


def test_impulse_log_records_qp_solves():
    """Controller should log at least one QP solve attempt."""
    target = make_iss_circular()
    chaser = make_chaser_offset_lvlh(target, dr_lvlh_km=np.array([0.0, -30.0e-3, 0.0]))
    cfg = default_mpc_cfg(target)
    res = simulate_terminal_phase(
        chaser_initial_eci=chaser, target_initial_eci=target,
        initial_quat=np.array([0., 0., 0., 1.]), initial_omega=np.zeros(3),
        inertia=INERTIA_SOYUZ, mpc_cfg=cfg, t_terminal=200.0,
        use_j2_for_target=False,
    )
    assert len(res.impulse_log) >= 1


def test_quaternion_stays_unit_norm_through_terminal():
    """Coupled propagator must keep |q|=1 even with thrust_callback firing."""
    target = make_iss_circular()
    chaser = make_chaser_offset_lvlh(target, dr_lvlh_km=np.array([0.0, -30.0e-3, 0.0]))
    cfg = default_mpc_cfg(target)
    res = simulate_terminal_phase(
        chaser_initial_eci=chaser, target_initial_eci=target,
        initial_quat=np.array([0., 0., 0., 1.]), initial_omega=np.array([0.01, -0.005, 0.002]),
        inertia=INERTIA_SOYUZ, mpc_cfg=cfg, t_terminal=300.0,
        use_j2_for_target=False,
    )
    qnorms = np.linalg.norm(res.coupled_states[6:10, :], axis=0)
    assert np.allclose(qnorms, 1.0, atol=1e-9)


def test_terminal_state_dict_shape():
    """terminal_lvlh dict has dr_lvlh, dv_lvlh as 3-vectors."""
    target = make_iss_circular()
    chaser = make_chaser_offset_lvlh(target, dr_lvlh_km=np.array([0.0, -20.0e-3, 0.0]))
    cfg = default_mpc_cfg(target)
    res = simulate_terminal_phase(
        chaser_initial_eci=chaser, target_initial_eci=target,
        initial_quat=np.array([0., 0., 0., 1.]), initial_omega=np.zeros(3),
        inertia=INERTIA_SOYUZ, mpc_cfg=cfg, t_terminal=150.0,
        use_j2_for_target=False,
    )
    assert res.terminal_lvlh['dr_lvlh'].shape == (3,)
    assert res.terminal_lvlh['dv_lvlh'].shape == (3,)
