"""Soyuz MS-17 end-to-end smoke test (Module 7 of F2-real).

Combines M5 (phasing reconstructor) + M6 (terminal-phase MPC) into a single
pipeline that reproduces the architectural Δv profile of an ultra-rapid
2-orbit Soyuz rendezvous to the ISS.

Placeholder initial conditions:
  - ISS at 420 km circular, inclination 51.6° (canonical 2020-10-14 epoch
    will be SGP4-propagated from a real TLE in F3-real once available).
  - Soyuz post-insertion at 200 km circular, same inclination, with phase
    angle ~10° behind ISS at insertion epoch (notional ahead/behind value).
  - Soyuz thrust 5.6e-5 km/s² (390 N / 7000 kg).

Reference (target Δv budget) — Murtazin (2020), unavailable as of May 2026:
  - Total Δv ≈ 110.7 m/s for ultra-rapid 2-orbit profile
  - Smoke test does NOT assert this value; only checks ΔV is in [50, 200]
    m/s and terminal_distance < 50 m.

When the actual Murtazin numbers and TLE arrive, swap make_iss_state and
make_soyuz_insertion_state for SGP4-derived states and tighten assertions.
"""
from dataclasses import dataclass
import numpy as np

from oosim.scenarios.phasing_reconstructor import (
    reconstruct_phasing, PhasingPlan,
)
from oosim.scenarios.terminal_handoff import (
    TerminalMPCConfig, TerminalSimResult, simulate_terminal_phase,
)
from oosim.proxops.coupled_state import MU_EARTH
from oosim.proxops.eci_propagator import propagate_orbit
from oosim.utils.frames_dynamic import lvlh_relative_to_eci_state

R_EARTH = 6378.137  # km
INERTIA_SOYUZ = np.diag([3850.0, 3920.0, 1240.0])  # kg·m²


@dataclass
class SoyuzMS17Result:
    """Full pipeline output."""
    phasing_plan: PhasingPlan
    terminal_result: TerminalSimResult
    total_dv_m_s: float                    # phasing impulsive + terminal sum
    total_dv_corrected_m_s: float          # finite-burn corrected total
    terminal_distance_m: float
    n_terminal_impulses: int
    transfer_duration_s: float


def make_iss_state(altitude_km: float = 420.0,
                   inclination_deg: float = 51.6,
                   true_anomaly_deg: float = 0.0) -> np.ndarray:
    """Build a circular ISS-like ECI state (placeholder for SGP4-from-TLE)."""
    a = R_EARTH + altitude_km
    v_circ = float(np.sqrt(MU_EARTH / a))
    inc = np.radians(inclination_deg)
    nu = np.radians(true_anomaly_deg)
    # Position in orbit plane, then rotate by inclination about x-axis
    r_perif = a * np.array([np.cos(nu), np.sin(nu), 0.0])
    v_perif = v_circ * np.array([-np.sin(nu), np.cos(nu), 0.0])
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(inc), -np.sin(inc)],
        [0, np.sin(inc), np.cos(inc)],
    ])
    return np.concatenate([Rx @ r_perif, Rx @ v_perif])


def make_soyuz_insertion_state(altitude_km: float = 200.0,
                                inclination_deg: float = 51.6,
                                phase_behind_iss_deg: float = 10.0) -> np.ndarray:
    """Build a notional Soyuz post-insertion ECI state (200 km circular)."""
    a = R_EARTH + altitude_km
    v_circ = float(np.sqrt(MU_EARTH / a))
    inc = np.radians(inclination_deg)
    nu = np.radians(-phase_behind_iss_deg)   # behind ISS in true anomaly
    r_perif = a * np.array([np.cos(nu), np.sin(nu), 0.0])
    v_perif = v_circ * np.array([-np.sin(nu), np.cos(nu), 0.0])
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(inc), -np.sin(inc)],
        [0, np.sin(inc), np.cos(inc)],
    ])
    return np.concatenate([Rx @ r_perif, Rx @ v_perif])


def run_soyuz_ms17_pipeline(
    *,
    iss_altitude_km: float = 420.0,
    soyuz_altitude_km: float = 200.0,
    inclination_deg: float = 51.6,
    soyuz_phase_behind_iss_deg: float = 10.0,
    thrust_acceleration: float = 5.6e-5,
    t_terminal: float = 400.0,   # 400 s = 3 × qp_dt (150 s) replanning cycles
    target_pos_lvlh_m: np.ndarray = None,
) -> SoyuzMS17Result:
    """Run the full Soyuz MS-17 end-to-end smoke pipeline."""
    if target_pos_lvlh_m is None:
        target_pos_lvlh_m = np.array([0.0, -10.0, 0.0])  # 10 m behind ISS on V-bar
    iss_state = make_iss_state(iss_altitude_km, inclination_deg, true_anomaly_deg=0.0)
    soyuz_state = make_soyuz_insertion_state(
        soyuz_altitude_km, inclination_deg, soyuz_phase_behind_iss_deg
    )
    # ── M5: phasing burns ──
    plan = reconstruct_phasing(
        chaser_state_eci=soyuz_state,
        target_state_eci=iss_state,
        thrust_acceleration=thrust_acceleration,
        use_j2=False,    # short transfer; J2 deferred
        n_eval_points=200,
    )
    # ── Propagate ISS to end-of-phasing ──
    iss_at_handoff = propagate_orbit(
        iss_state, np.array([0.0, plan.transfer_time]),
        mu=MU_EARTH, include_j2=False,
    )[-1]
    # ── Terminal handoff initial state ──
    # After phasing the chaser is on the ISS orbit but ~670 km behind in
    # true anomaly (no phase-matching in M5 v1).  The terminal MPC is
    # designed for the last ~km of approach, so we initialise it from a
    # notional V-bar hold point 50 m behind ISS at the handoff epoch.
    # This is physically representative of where the real profile would hand
    # off after the phase-matching + far-range station-keeping sequence
    # (those manoeuvres are not modelled in F2-real M5).
    # LVLH offset: [0, -50 m, 0] = 50 m behind on V-bar; zero relative velocity
    # (CW drift-stable hold on the same circular orbit).
    terminal_offset_lvlh_km = np.array([0.0, -0.05, 0.0])   # km, 50 m behind on V-bar
    terminal_rel_lvlh_km = np.concatenate([terminal_offset_lvlh_km, np.zeros(3)])
    r_chaser_term, v_chaser_term = lvlh_relative_to_eci_state(
        terminal_rel_lvlh_km,
        iss_at_handoff[:3],
        iss_at_handoff[3:6],
        mu=MU_EARTH,
    )
    chaser_terminal_eci = np.concatenate([r_chaser_term, v_chaser_term])
    # ── M6: terminal MPC ──
    a_iss = float(np.linalg.norm(iss_at_handoff[:3]))
    n_iss = float(np.sqrt(MU_EARTH / a_iss**3))
    mpc_cfg = TerminalMPCConfig(
        target_pos_lvlh=target_pos_lvlh_m,
        target_n=n_iss,
        qp_dt=150.0,
        qp_horizon_steps=3,
        qp_dv_max_per_step=0.3,
        thrust_acceleration=thrust_acceleration,
        # ECOS converges reliably for offsets ≤ 50 m (HCW validity range).
        # SCS diverges at this scale due to inaccurate first-step solutions.
    )
    term = simulate_terminal_phase(
        chaser_initial_eci=chaser_terminal_eci,
        target_initial_eci=iss_at_handoff,
        initial_quat=np.array([0., 0., 0., 1.]),
        initial_omega=np.zeros(3),
        inertia=INERTIA_SOYUZ,
        mpc_cfg=mpc_cfg,
        t_terminal=t_terminal,
        n_eval_points=200,
        use_j2_for_target=False,
    )
    # ── Aggregate Δv ──
    phasing_dv_imp_m_s = plan.total_dv_impulsive * 1000.0
    phasing_dv_corr_m_s = plan.total_dv_corrected * 1000.0
    terminal_dv_m_s = sum(
        float(np.linalg.norm(e.dv_lvlh_m_s)) for e in term.impulse_log
    )
    total_dv = phasing_dv_imp_m_s + terminal_dv_m_s
    total_dv_corr = phasing_dv_corr_m_s + terminal_dv_m_s
    return SoyuzMS17Result(
        phasing_plan=plan,
        terminal_result=term,
        total_dv_m_s=total_dv,
        total_dv_corrected_m_s=total_dv_corr,
        terminal_distance_m=term.terminal_distance_m,
        n_terminal_impulses=len([e for e in term.impulse_log if e.duration_s > 0]),
        transfer_duration_s=plan.transfer_time + t_terminal,
    )


def report(result: SoyuzMS17Result) -> str:
    """Format a one-page text report of the pipeline outcome."""
    lines = [
        "╔══════════════════════════════════════════════════════════════════╗",
        "║  Soyuz MS-17 end-to-end smoke test (Option C, F2-real Module 7)  ║",
        "╚══════════════════════════════════════════════════════════════════╝",
        "",
        f"Phasing (M5 — Hohmann + finite-burn correction):",
        f"  Burn 1: {result.phasing_plan.burns[0].label:<22} "
        f"|Δv|_imp = {result.phasing_plan.burns[0].dv_magnitude_impulsive*1000:7.2f} m/s, "
        f"|Δv|_corr = {result.phasing_plan.burns[0].dv_magnitude_corrected*1000:7.2f} m/s, "
        f"t_burn = {result.phasing_plan.burns[0].duration:6.1f} s",
        f"  Burn 2: {result.phasing_plan.burns[1].label:<22} "
        f"|Δv|_imp = {result.phasing_plan.burns[1].dv_magnitude_impulsive*1000:7.2f} m/s, "
        f"|Δv|_corr = {result.phasing_plan.burns[1].dv_magnitude_corrected*1000:7.2f} m/s, "
        f"t_burn = {result.phasing_plan.burns[1].duration:6.1f} s",
        f"  Phasing total Δv (imp):    {result.phasing_plan.total_dv_impulsive*1000:7.2f} m/s",
        f"  Phasing total Δv (corr):   {result.phasing_plan.total_dv_corrected*1000:7.2f} m/s",
        f"  Transfer time:             {result.phasing_plan.transfer_time:7.1f} s",
        "",
        f"Terminal phase (M6 — coupled-state MPC handoff):",
        f"  # impulses fired:          {result.n_terminal_impulses}",
        f"  Terminal distance:         {result.terminal_distance_m:7.2f} m",
        "",
        f"Aggregate:",
        f"  Total Δv (imp + terminal): {result.total_dv_m_s:7.2f} m/s",
        f"  Total Δv (corr + terminal):{result.total_dv_corrected_m_s:7.2f} m/s",
        f"  Mission duration:          {result.transfer_duration_s/60:6.1f} min",
        "",
        f"Reference: Murtazin (2020) reports ≈110.7 m/s for ultra-rapid 2-orbit",
        f"           Soyuz profile. PDF currently inaccessible — value is",
        f"           qualitative target only.",
    ]
    return "\n".join(lines)
