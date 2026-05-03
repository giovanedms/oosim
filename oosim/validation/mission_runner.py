"""Common runner for F3-real mission reproductions.

A MissionScenario describes the inputs needed to reproduce one historical
RPOD mission end-to-end with the M5-M8-M6 pipeline. validate_mission()
runs the pipeline and compares the simulator-produced Δv against a
reference (published or reverse-engineered) within the scenario's tier
tolerance.

Tiers:
  - TIER_A: published Δv reference, tolerance ≤ 5%.
  - TIER_B: reverse-engineered Δv from public mass+ΔH+TOF, tolerance 15-25%.
  - TIER_C: qualitative check only (no numeric assertion).
"""
import numpy as np

from oosim.validation.types import (
    ValidationTier, MissionScenario, MissionRunResult, ValidationReport,
)
from oosim.scenarios.phasing_reconstructor import reconstruct_phasing
from oosim.scenarios.phasing_drift import compute_phasing_burns
from oosim.scenarios.terminal_handoff import (
    TerminalMPCConfig, simulate_terminal_phase,
)
from oosim.proxops.coupled_state import MU_EARTH
from oosim.proxops.eci_propagator import propagate_orbit

# Re-export types so callers can do `from oosim.validation.mission_runner import ...`
__all__ = [
    "ValidationTier", "MissionScenario", "MissionRunResult", "ValidationReport",
    "run_mission", "validate_mission", "_TOLERANCE_BY_TIER",
]

_TOLERANCE_BY_TIER = {
    ValidationTier.TIER_A: (0.05, 0.10),    # ±5% Δv, ±10% duration
    ValidationTier.TIER_B: (0.20, 0.25),    # ±20% Δv, ±25% duration
    ValidationTier.TIER_C: (np.inf, np.inf),
}


def run_mission(scenario: MissionScenario) -> MissionRunResult:
    """Execute the M5 → M8 → M6 pipeline for the scenario."""
    # M5: Hohmann phasing
    plan = reconstruct_phasing(
        chaser_state_eci=scenario.chaser_initial_eci,
        target_state_eci=scenario.target_initial_eci,
        thrust_acceleration=scenario.thrust_acceleration,
        use_j2=False,
        n_eval_points=200,
    )
    chaser_after_phasing = plan.chaser_trajectory_x[:, -1]
    target_at_handoff = propagate_orbit(
        scenario.target_initial_eci, np.array([0.0, plan.transfer_time]),
        mu=MU_EARTH, include_j2=False,
    )[-1]
    # M8: phasing-drift loop
    drift = compute_phasing_burns(
        chaser_state_eci=chaser_after_phasing,
        target_state_eci=target_at_handoff,
        thrust_acceleration=scenario.thrust_acceleration,
        n_phase_orbits=scenario.n_phase_orbits,
        mu=MU_EARTH,
    )
    chaser_at_terminal = drift.chaser_final_eci
    target_at_terminal = drift.target_final_eci
    # M6: terminal-phase MPC
    a_t = float(np.linalg.norm(target_at_terminal[:3]))
    n_t = float(np.sqrt(MU_EARTH / a_t**3))
    mpc_cfg = TerminalMPCConfig(
        target_pos_lvlh=scenario.target_pos_lvlh_m,
        target_n=n_t,
        qp_dt=150.0,
        qp_horizon_steps=3,
        qp_dv_max_per_step=0.3,
        thrust_acceleration=scenario.thrust_acceleration,
    )
    term = simulate_terminal_phase(
        chaser_initial_eci=chaser_at_terminal,
        target_initial_eci=target_at_terminal,
        initial_quat=np.array([0., 0., 0., 1.]),
        initial_omega=np.zeros(3),
        inertia=scenario.inertia,
        mpc_cfg=mpc_cfg,
        t_terminal=scenario.t_terminal,
        n_eval_points=200,
        use_j2_for_target=False,
    )
    phasing_dv_m_s = plan.total_dv_impulsive * 1000.0
    drift_dv_m_s = sum(b.dv_magnitude_impulsive for b in drift.burns) * 1000.0
    terminal_dv_m_s = sum(
        float(np.linalg.norm(e.dv_lvlh_m_s)) for e in term.impulse_log
    )
    total_dv = phasing_dv_m_s + drift_dv_m_s + terminal_dv_m_s
    return MissionRunResult(
        phasing_dv_m_s=phasing_dv_m_s,
        drift_dv_m_s=drift_dv_m_s,
        terminal_dv_m_s=terminal_dv_m_s,
        total_dv_m_s=total_dv,
        phasing_time_s=plan.transfer_time,
        drift_time_s=drift.drift_time,
        total_duration_s=plan.transfer_time + drift.drift_time + scenario.t_terminal,
        terminal_distance_m=term.terminal_distance_m,
        n_terminal_impulses=len([e for e in term.impulse_log if e.duration_s > 0]),
    )


def validate_mission(scenario: MissionScenario) -> ValidationReport:
    """Run pipeline and produce ValidationReport with tier-specific assertions."""
    res = run_mission(scenario)
    tol_dv, tol_dur = _TOLERANCE_BY_TIER[scenario.tier]
    dv_err = (res.total_dv_m_s - scenario.expected_dv_total_m_s) / scenario.expected_dv_total_m_s
    sim_dur_min = res.total_duration_s / 60.0
    dur_err = (sim_dur_min - scenario.expected_duration_min) / scenario.expected_duration_min
    passed_dv = abs(dv_err) <= tol_dv
    passed_dur = abs(dur_err) <= tol_dur
    passed_all = passed_dv and passed_dur
    summary = (
        f"{scenario.name} (Tier {scenario.tier.value}): "
        f"Δv sim={res.total_dv_m_s:.1f} m/s vs ref={scenario.expected_dv_total_m_s:.1f} m/s "
        f"err={dv_err*100:+.1f}% (tol ±{tol_dv*100:.0f}%) [{('PASS' if passed_dv else 'FAIL')}]; "
        f"duration sim={sim_dur_min:.1f} min vs ref={scenario.expected_duration_min:.1f} min "
        f"err={dur_err*100:+.1f}% (tol ±{tol_dur*100:.0f}%) [{('PASS' if passed_dur else 'FAIL')}]"
    )
    return ValidationReport(
        scenario=scenario, result=res,
        dv_error_relative=dv_err,
        duration_error_relative=dur_err,
        tolerance_dv=tol_dv, tolerance_duration=tol_dur,
        passed_dv=passed_dv, passed_duration=passed_dur,
        passed_overall=passed_all, summary=summary,
    )
