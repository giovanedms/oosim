"""Mission phasing reconstructor (Module 5 of F2-real).

Given chaser and target ECI insertion states, computes a Hohmann two-impulse
phasing burn sequence (with finite-burn correction) to bring the chaser onto
the target's orbit. Burns are CALCULATED from orbital mechanics, not replayed
from published data — this is the architectural point of Option C.

Pipeline:
  1. Extract chaser and target semi-major axes from cartesian state.
  2. Compute Hohmann delta-v at apogee/perigee tangent points.
  3. Apply finite-burn correction (Vallado Eq. 6-79) given thrust acceleration.
  4. Propagate chaser through burn epochs using ECI propagator (Kepler+J2).
  5. At handoff (end of phasing transfer), compute LVLH relative state.

Limitations of this v1 reconstructor:
  - Coplanar transfer only (no plane-change burns).
  - Two-impulse Hohmann (no bi-elliptic, no Lambert targeting).
  - Phase-matching assumed already satisfied (no phasing-orbit drift loop).
  - Target propagated with same J2 model as chaser.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from oosim.proxops.eci_propagator import propagate_orbit, MU_EARTH
from oosim.phasing.hohmann import hohmann_dv, hohmann_time_of_flight
from oosim.phasing.finite_burn import finite_burn_corrected_dv
from oosim.utils.frames_dynamic import eci_state_to_lvlh_relative
from oosim.utils.frames_extra import cartesian_to_keplerian


@dataclass
class ImpulseEvent:
    """One burn in the reconstructed plan."""
    epoch: float                # seconds from t0
    dv_eci: np.ndarray          # 3-vector [km/s], delivered Δv in ECI
    dv_magnitude_impulsive: float   # idealised |Δv| [km/s]
    dv_magnitude_corrected: float   # finite-burn corrected |Δv| [km/s]
    duration: float             # burn duration [s] for finite-burn execution
    label: str                  # 'perigee_raise' | 'apogee_circularise' | etc.


@dataclass
class PhasingPlan:
    """Output of reconstruct_phasing()."""
    burns: list[ImpulseEvent]
    transfer_time: float        # Hohmann TOF [s]
    total_dv_impulsive: float   # sum of impulsive |Δv| [km/s]
    total_dv_corrected: float   # sum of finite-burn corrected |Δv| [km/s]
    chaser_trajectory_t: np.ndarray   # times [s], shape (N,)
    chaser_trajectory_x: np.ndarray   # ECI states [km, km/s], shape (6, N)
    target_trajectory_x: np.ndarray   # ECI target propagated, shape (6, N)
    terminal_lvlh: dict         # output of eci_state_to_lvlh_relative at handoff


def reconstruct_phasing(
    chaser_state_eci: np.ndarray,        # shape (6,) [km, km/s]
    target_state_eci: np.ndarray,        # shape (6,) [km, km/s]
    thrust_acceleration: float,          # [km/s²], constant during burns
    *,
    use_j2: bool = True,
    n_eval_points: int = 200,
) -> PhasingPlan:
    """Reconstruct a Hohmann phasing transfer between coplanar near-circular orbits.

    Steps:
      1. r_chaser = ||chaser pos||, r_target = ||target pos|| at t=0
      2. dv1, dv2 = hohmann_dv(r_chaser, r_target, MU_EARTH)
      3. Apply finite-burn corrections (Vallado Eq. 6-79) — get dv1_corr, dv2_corr
      4. Burn 1 at t=0: thrust along chaser velocity unit-vector.
         Apply impulsive Δv to chaser state, then propagate to t = TOF.
      5. Burn 2 at t=TOF: thrust along chaser velocity unit-vector at that point.
         Apply impulsive Δv. Final state is on the target orbit.
      6. Target propagated with Kepler+J2 over [0, TOF] for relative-state output.
      7. Compute LVLH relative state at handoff.

    Direction convention for Hohmann:
      - If r_chaser < r_target: dv1 raises perigee→apogee (prograde at periapsis),
        dv2 circularises at apogee (prograde at new apoapsis). Both prograde.
      - If r_chaser > r_target: both retrograde (lowering orbit).

    Returns PhasingPlan with full trajectories and terminal LVLH state.

    Notes on unit conventions:
      - hohmann_dv returns Δv in km/s.
      - finite_burn_corrected_dv expects dv_impulsive in m/s, returns m/s.
      - thrust_acceleration is in km/s²; converted to m/s² for finite_burn_corrected_dv.
      - burn_duration is computed as dv_corrected_km_s / thrust_acceleration_km_s2.
    """
    chaser_state_eci = np.asarray(chaser_state_eci, dtype=float)
    target_state_eci = np.asarray(target_state_eci, dtype=float)

    # ── Step 1: extract orbital radii ──────────────────────────────────────────
    r_chaser = float(np.linalg.norm(chaser_state_eci[:3]))
    r_target = float(np.linalg.norm(target_state_eci[:3]))

    # ── Step 2: Hohmann impulsive Δv (km/s) ───────────────────────────────────
    dv1_km_s, dv2_km_s, _ = hohmann_dv(r_chaser, r_target, MU_EARTH)
    tof = hohmann_time_of_flight(r_chaser, r_target, MU_EARTH)

    # Sign convention: prograde for raising, retrograde for lowering.
    # hohmann_dv returns magnitudes; direction is determined by which orbit is higher.
    raising = r_target > r_chaser
    sign = 1.0 if raising else -1.0

    # ── Step 3: finite-burn corrections ───────────────────────────────────────
    # v_circ at burn 1 altitude (chaser initial radius)
    v_circ_1_km_s = float(np.sqrt(MU_EARTH / r_chaser))
    # v_circ at burn 2 altitude (target radius = apogee of transfer ellipse)
    v_circ_2_km_s = float(np.sqrt(MU_EARTH / r_target))

    # finite_burn_corrected_dv works in m/s; thrust_acceleration in km/s² → m/s²
    thrust_accel_m_s2 = thrust_acceleration * 1000.0
    dv1_m_s = dv1_km_s * 1000.0
    dv2_m_s = dv2_km_s * 1000.0

    dv1_corr_m_s = finite_burn_corrected_dv(dv1_m_s, thrust_accel_m_s2, v_circ_1_km_s)
    dv2_corr_m_s = finite_burn_corrected_dv(dv2_m_s, thrust_accel_m_s2, v_circ_2_km_s)

    dv1_corr_km_s = dv1_corr_m_s / 1000.0
    dv2_corr_km_s = dv2_corr_m_s / 1000.0

    # Burn duration: duration = dv / a  (constant-thrust, constant-mass approx.)
    dur1 = dv1_corr_km_s / thrust_acceleration
    dur2 = dv2_corr_km_s / thrust_acceleration

    # ── Step 4: Burn 1 at t=0 ─────────────────────────────────────────────────
    v0 = chaser_state_eci[3:6]
    v0_norm = float(np.linalg.norm(v0))
    v0_hat = v0 / v0_norm   # unit velocity = prograde direction

    dv1_vec_km_s = sign * dv1_km_s * v0_hat    # impulsive Δv vector [km/s]

    # Post-burn-1 state: apply impulsive Δv instantaneously
    chaser_post_burn1 = chaser_state_eci.copy()
    chaser_post_burn1[3:6] += dv1_vec_km_s

    # Determine labels based on transfer direction
    label1 = 'perigee_raise' if raising else 'perigee_lower'
    label2 = 'apogee_circularise' if raising else 'perigee_circularise'

    burn1 = ImpulseEvent(
        epoch=0.0,
        dv_eci=dv1_vec_km_s,
        dv_magnitude_impulsive=dv1_km_s,
        dv_magnitude_corrected=dv1_corr_km_s,
        duration=dur1,
        label=label1,
    )

    # ── Step 5: Propagate chaser post-burn-1 to t=TOF, then apply Burn 2 ─────
    # Build t_array for chaser trajectory (two segments: pre-burn2 propagation)
    # Segment: [0, TOF] propagated from post-burn-1 state
    t_array = np.linspace(0.0, tof, n_eval_points)

    # Propagate chaser from post-burn-1 state across [0, TOF]
    chaser_transfer_states = propagate_orbit(
        chaser_post_burn1, t_array, mu=MU_EARTH, include_j2=use_j2
    )  # shape (N, 6)

    # State at end of transfer (just before burn 2)
    chaser_at_tof = chaser_transfer_states[-1]   # (6,)

    # Direction at burn 2: velocity unit-vector at TOF
    v_tof = chaser_at_tof[3:6]
    v_tof_hat = v_tof / float(np.linalg.norm(v_tof))

    dv2_vec_km_s = sign * dv2_km_s * v_tof_hat  # impulsive Δv vector [km/s]

    burn2 = ImpulseEvent(
        epoch=tof,
        dv_eci=dv2_vec_km_s,
        dv_magnitude_impulsive=dv2_km_s,
        dv_magnitude_corrected=dv2_corr_km_s,
        duration=dur2,
        label=label2,
    )

    # Apply burn 2 impulsively to get terminal chaser state
    chaser_terminal = chaser_at_tof.copy()
    chaser_terminal[3:6] += dv2_vec_km_s

    # Append terminal state to trajectory (replace last point with post-burn state)
    # The trajectory array represents the chaser coasting on the transfer ellipse
    # plus the final circularised state.
    chaser_traj_states = chaser_transfer_states.copy()
    chaser_traj_states[-1] = chaser_terminal   # overwrite last with post-burn2

    # ── Step 6: Propagate target over same time array ─────────────────────────
    target_traj_states = propagate_orbit(
        target_state_eci, t_array, mu=MU_EARTH, include_j2=use_j2
    )  # shape (N, 6)

    # ── Step 7: Compute LVLH relative state at handoff ────────────────────────
    r_chaser_term = chaser_terminal[:3]
    v_chaser_term = chaser_terminal[3:6]
    r_target_term = target_traj_states[-1, :3]
    v_target_term = target_traj_states[-1, 3:6]

    rel_6vec = eci_state_to_lvlh_relative(
        r_chaser_term, v_chaser_term, r_target_term, v_target_term, mu=MU_EARTH
    )
    terminal_lvlh = {
        'dr_lvlh': rel_6vec[:3],
        'dv_lvlh': rel_6vec[3:6],
    }

    # ── Assemble output ───────────────────────────────────────────────────────
    # Transpose trajectories from (N, 6) to (6, N) as specified in PhasingPlan
    chaser_traj_x = chaser_traj_states.T   # (6, N)
    target_traj_x = target_traj_states.T   # (6, N)

    total_dv_imp = dv1_km_s + dv2_km_s
    total_dv_corr = dv1_corr_km_s + dv2_corr_km_s

    return PhasingPlan(
        burns=[burn1, burn2],
        transfer_time=tof,
        total_dv_impulsive=total_dv_imp,
        total_dv_corrected=total_dv_corr,
        chaser_trajectory_t=t_array,
        chaser_trajectory_x=chaser_traj_x,
        target_trajectory_x=target_traj_x,
        terminal_lvlh=terminal_lvlh,
    )
