"""Approach-corridor entry maneuver (Module 9 of F3-real).

Bridges M8 (phasing-orbit drift loop) and M6 (terminal-phase MPC). M8 brings
the chaser to within metres of the target; M6 expects the chaser to enter
the approach corridor at a known LVLH hold point (typically 50-100 m on
V-bar) with near-zero relative velocity. M9 computes the two-impulse HCW
transfer from M8's output state to that hold point.

Algorithm (HCW closed-form two-impulse rendezvous, Curtis §7.4 / Vallado §6.7):

    Given r1, v1 (current LVLH state) and r2, v2 (desired LVLH state at
    time tf), the HCW state-transition matrix Φ(tf) decomposes as

        [r2]   [Φ_rr  Φ_rv] [r1]
        [v2] = [Φ_vr  Φ_vv] [v1+]

    where v1+ is the velocity immediately after the first impulse. Solving
    for v1+ requires Φ_rv to be invertible (it is for n·tf ∉ {0, 2π}):

        v1+ = Φ_rv⁻¹ · (r2 - Φ_rr · r1)

    Then the arrival velocity is

        v2- = Φ_vr · r1 + Φ_vv · v1+

    and the two impulses are

        Δv1 = v1+ - v1
        Δv2 = v2 - v2-

References:
    Curtis, H. D. (2020). Orbital Mechanics for Engineering Students,
        4th ed., Butterworth-Heinemann. §7.4 (two-impulse rendezvous).
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed.,
        Microcosm Press. §6.7 (Hill-Clohessy-Wiltshire targeting).
"""
from dataclasses import dataclass
import numpy as np

from oosim.proxops.coupled_state import MU_EARTH
from oosim.proxops.eci_propagator import propagate_orbit
from oosim.proxops.hcw import hcw_state_transition_matrix
from oosim.utils.frames_dynamic import (
    eci_state_to_lvlh_relative, lvlh_relative_to_eci_state,
)
from oosim.utils.frames import eci_to_lvlh_rotation
from oosim.phasing.finite_burn import finite_burn_corrected_dv
from oosim.scenarios.phasing_reconstructor import ImpulseEvent


@dataclass
class CorridorEntryPlan:
    burns: list                      # [ImpulseEvent, ImpulseEvent]
    transfer_time: float             # tf [s]
    initial_relative_state_lvlh: np.ndarray   # 6-vec at M9 start [km, km/s]
    final_relative_state_lvlh: np.ndarray     # 6-vec at M9 end (≈ hold point) [km, km/s]
    chaser_final_eci: np.ndarray
    target_final_eci: np.ndarray
    total_dv_m_s: float


def enter_approach_corridor(
    chaser_state_eci: np.ndarray,        # (6,) [km, km/s]
    target_state_eci: np.ndarray,        # (6,) [km, km/s]
    hold_point_lvlh_m: np.ndarray,       # (3,) [m]  desired LVLH position at end
    *,
    transfer_time_s: float = 600.0,      # 10 min default
    thrust_acceleration: float = 5.6e-5, # km/s²
    arrival_velocity_lvlh_m_s: np.ndarray | None = None,  # default zero
    mu: float = MU_EARTH,
) -> CorridorEntryPlan:
    """Two-impulse HCW transfer from current state to LVLH hold point.

    Both objects propagate two-body during the transfer. Impulses are
    rotated LVLH→ECI and applied instantaneously to the chaser ECI state.

    Args:
        chaser_state_eci, target_state_eci: 6-vectors at start [km, km/s].
        hold_point_lvlh_m: 3-vector LVLH position at end [m].
        transfer_time_s: free-flight duration between the two impulses [s].
        thrust_acceleration: body-frame max accel for finite-burn correction [km/s²].
        arrival_velocity_lvlh_m_s: 3-vec LVLH velocity at arrival [m/s] (default 0).
        mu: gravitational parameter [km³/s²].

    Returns:
        CorridorEntryPlan with both burns, ECI states pre/post, and Δv totals.
    """
    if arrival_velocity_lvlh_m_s is None:
        arrival_velocity_lvlh_m_s = np.zeros(3)
    # ── 1. current relative state in LVLH (km, km/s) ─────────────────────────
    rel0_km = eci_state_to_lvlh_relative(
        chaser_state_eci[:3], chaser_state_eci[3:6],
        target_state_eci[:3], target_state_eci[3:6], mu=mu,
    )
    r1 = rel0_km[:3]
    v1 = rel0_km[3:6]
    # Desired final state (km, km/s)
    r2 = np.asarray(hold_point_lvlh_m, dtype=float) / 1000.0
    v2 = np.asarray(arrival_velocity_lvlh_m_s, dtype=float) / 1000.0
    # ── 2. HCW STM and two-impulse solution ──────────────────────────────────
    a_target = float(np.linalg.norm(target_state_eci[:3]))
    n = float(np.sqrt(mu / a_target**3))
    nt = n * transfer_time_s
    if abs(np.sin(nt)) < 1e-9:
        raise ValueError(
            f"transfer_time {transfer_time_s} s is a singular point of HCW "
            f"(n·t = {nt:.4f} rad ≈ kπ); pick a different duration."
        )
    Phi = hcw_state_transition_matrix(n, transfer_time_s)
    Phi_rr = Phi[:3, :3]
    Phi_rv = Phi[:3, 3:]
    Phi_vr = Phi[3:, :3]
    Phi_vv = Phi[3:, 3:]
    v1_plus = np.linalg.solve(Phi_rv, r2 - Phi_rr @ r1)
    v2_minus = Phi_vr @ r1 + Phi_vv @ v1_plus
    dv1_lvlh_km_s = v1_plus - v1
    dv2_lvlh_km_s = v2 - v2_minus
    # ── 3. apply impulse 1 in ECI ────────────────────────────────────────────
    R_eci_to_lvlh_t0 = eci_to_lvlh_rotation(target_state_eci[:3], target_state_eci[3:6])
    dv1_eci_km_s = R_eci_to_lvlh_t0.T @ dv1_lvlh_km_s
    chaser_post_burn1 = chaser_state_eci.copy()
    chaser_post_burn1[3:6] += dv1_eci_km_s
    # ── 4. propagate both objects across transfer_time ───────────────────────
    chaser_arrival = propagate_orbit(
        chaser_post_burn1, np.array([0.0, transfer_time_s]),
        mu=mu, include_j2=False,
    )[-1]
    target_arrival = propagate_orbit(
        target_state_eci, np.array([0.0, transfer_time_s]),
        mu=mu, include_j2=False,
    )[-1]
    # ── 5. apply impulse 2 in ECI ────────────────────────────────────────────
    R_eci_to_lvlh_tf = eci_to_lvlh_rotation(target_arrival[:3], target_arrival[3:6])
    dv2_eci_km_s = R_eci_to_lvlh_tf.T @ dv2_lvlh_km_s
    chaser_final = chaser_arrival.copy()
    chaser_final[3:6] += dv2_eci_km_s
    # ── 6. measure achieved final state (sanity) ─────────────────────────────
    rel_final_km = eci_state_to_lvlh_relative(
        chaser_final[:3], chaser_final[3:6],
        target_arrival[:3], target_arrival[3:6], mu=mu,
    )
    # ── 7. finite-burn corrections + impulse events ──────────────────────────
    thrust_accel_m_s2 = thrust_acceleration * 1000.0
    v_circ_km_s = float(np.sqrt(mu / a_target))
    dv1_mag_km_s = float(np.linalg.norm(dv1_eci_km_s))
    dv2_mag_km_s = float(np.linalg.norm(dv2_eci_km_s))
    if dv1_mag_km_s > 1e-12:
        dv1_corr_m_s = finite_burn_corrected_dv(
            dv1_mag_km_s * 1000.0, thrust_accel_m_s2, v_circ_km_s,
        )
        dv1_corr_km_s = dv1_corr_m_s / 1000.0
        dur1 = dv1_corr_km_s / thrust_acceleration
    else:
        dv1_corr_km_s = 0.0
        dur1 = 0.0
    if dv2_mag_km_s > 1e-12:
        dv2_corr_m_s = finite_burn_corrected_dv(
            dv2_mag_km_s * 1000.0, thrust_accel_m_s2, v_circ_km_s,
        )
        dv2_corr_km_s = dv2_corr_m_s / 1000.0
        dur2 = dv2_corr_km_s / thrust_acceleration
    else:
        dv2_corr_km_s = 0.0
        dur2 = 0.0
    burn1 = ImpulseEvent(
        epoch=0.0, dv_eci=dv1_eci_km_s,
        dv_magnitude_impulsive=dv1_mag_km_s,
        dv_magnitude_corrected=dv1_corr_km_s,
        duration=dur1, label='corridor_depart',
    )
    burn2 = ImpulseEvent(
        epoch=transfer_time_s, dv_eci=dv2_eci_km_s,
        dv_magnitude_impulsive=dv2_mag_km_s,
        dv_magnitude_corrected=dv2_corr_km_s,
        duration=dur2, label='corridor_arrive',
    )
    total_dv_m_s = (dv1_mag_km_s + dv2_mag_km_s) * 1000.0
    return CorridorEntryPlan(
        burns=[burn1, burn2],
        transfer_time=transfer_time_s,
        initial_relative_state_lvlh=rel0_km,
        final_relative_state_lvlh=rel_final_km,
        chaser_final_eci=chaser_final,
        target_final_eci=target_arrival,
        total_dv_m_s=total_dv_m_s,
    )
