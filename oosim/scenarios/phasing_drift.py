"""Phasing-orbit drift loop (Module 8 of F3-real, Vallado §6.6.1).

Closes the phase-matching gap left by M5 v1. After a Hohmann transfer the
chaser is on the target's altitude but offset by Δθ in true anomaly; this
module computes a co-elliptic phasing maneuver (2 tangential burns separated
by k drift orbits) to bring the chaser within metres of the target.

Algorithm (Vallado, Fundamentals of Astrodynamics, 5th ed., §6.6.1):

    1. measure Δθ_lead = signed angular separation (positive = chaser ahead)
    2. T_phase = T_target * (1 + Δθ_lead/(2π·k))
       chaser behind (Δθ<0) → T_phase < T_target → smaller orbit, faster, catches up
       chaser ahead (Δθ>0) → T_phase > T_target → larger orbit, slower, lets target catch up
    3. a_phase = (μ·T_phase²/(4π²))^(1/3)
    4. Δv1 = v_phase(r) - v_chaser(r)   tangential at current chaser point
    5. coast k orbits in phasing ellipse
    6. Δv2 = -Δv1                       re-circularise at same r
    7. apply finite-burn correction to both magnitudes

References:
    Vallado, D. A. (2022). Fundamentals of Astrodynamics, 5th ed.,
        Microcosm Press. §6.6.1 (Phasing maneuver), Eq. 6-79 (finite-burn loss).
"""
from dataclasses import dataclass
import numpy as np

from oosim.proxops.eci_propagator import propagate_orbit, MU_EARTH
from oosim.phasing.finite_burn import finite_burn_corrected_dv
from oosim.scenarios.phasing_reconstructor import ImpulseEvent


@dataclass
class PhasingDriftPlan:
    burns: list                 # [ImpulseEvent, ImpulseEvent]
    drift_time: float           # k × T_phase [s]
    n_phase_orbits: int
    delta_theta_initial_deg: float    # measured Δθ_lead at t=0 (positive=ahead)
    chaser_final_eci: np.ndarray      # post-burn-2 chaser ECI state [km, km/s]
    target_final_eci: np.ndarray      # target propagated to t = drift_time
    relative_distance_final_m: float  # ||r_chaser - r_target|| at end


def measure_phase_angle_deg(chaser_state_eci: np.ndarray,
                             target_state_eci: np.ndarray) -> float:
    """Return phase angle of chaser relative to target in degrees.

    Positive: chaser is AHEAD of target (larger true anomaly).
    Negative: chaser is BEHIND target.

    Computed in the orbit plane (uses target's angular momentum direction).
    Result is wrapped to (-180, +180].
    """
    r_c = np.asarray(chaser_state_eci[:3], dtype=float)
    r_t = np.asarray(target_state_eci[:3], dtype=float)
    v_t = np.asarray(target_state_eci[3:6], dtype=float)
    h_t = np.cross(r_t, v_t)              # angular momentum direction
    h_hat = h_t / np.linalg.norm(h_t)
    # Unsigned angle
    cos_a = np.clip(np.dot(r_c, r_t) / (np.linalg.norm(r_c) * np.linalg.norm(r_t)), -1.0, 1.0)
    a_unsigned = np.degrees(np.arccos(cos_a))
    # Sign: + if r_t × r_c is along +h_hat (chaser ahead in motion sense)
    cross = np.cross(r_t, r_c)
    sign = float(np.sign(np.dot(cross, h_hat)))
    if sign == 0.0:
        sign = 1.0
    val = sign * a_unsigned
    # wrap to (-180, 180]
    if val > 180.0:
        val -= 360.0
    if val <= -180.0:
        val += 360.0
    return val


def compute_phasing_burns(
    chaser_state_eci: np.ndarray,        # (6,) [km, km/s] — assumed near-circular at target altitude
    target_state_eci: np.ndarray,        # (6,) [km, km/s]
    thrust_acceleration: float,          # body-frame thrust accel [km/s²]
    *,
    n_phase_orbits: int = 2,
    mu: float = MU_EARTH,
) -> PhasingDriftPlan:
    """Compute and execute the co-elliptic phasing-drift maneuver.

    Returns a PhasingDriftPlan with the two burns, drift time, and final
    chaser/target states (after re-circularisation). Both objects propagate
    Keplerian (two-body) — use J2 separately if needed in higher-fidelity work.
    """
    # 1. Phase angle (deg) — chaser relative to target
    dtheta_deg = measure_phase_angle_deg(chaser_state_eci, target_state_eci)
    dtheta_rad = np.radians(dtheta_deg)
    # 2. Target orbit period
    r_t = float(np.linalg.norm(target_state_eci[:3]))
    a_t = r_t                              # circular assumption
    T_target = 2.0 * np.pi * np.sqrt(a_t**3 / mu)
    # 3. Phasing-orbit period
    k = int(n_phase_orbits)
    if k < 1:
        raise ValueError("n_phase_orbits must be >= 1")
    # Vallado §6.6.1: phasing period adjusted so that after k orbits the
    # angular gap closes. Sign convention: Δθ_lead > 0 = chaser ahead →
    # need larger orbit (slower) → T_phase > T_target.
    # Δθ_lead < 0 = chaser behind → need smaller orbit (faster) →
    # T_phase < T_target.
    T_phase = T_target * (1.0 + dtheta_rad / (2.0 * np.pi * k))
    if T_phase <= 0.0:
        raise ValueError(
            f"phasing requires T_phase>0 (got {T_phase:.1f}s); "
            f"reduce n_phase_orbits or lead by less than k revolutions"
        )
    # 4. Phasing semi-major axis
    a_phase = (mu * T_phase**2 / (4.0 * np.pi**2))**(1.0 / 3.0)
    # 5. Tangential speeds at chaser's current radius (using r = r_chaser ~ r_target)
    r_c = float(np.linalg.norm(chaser_state_eci[:3]))
    v_chaser_circ_km_s = float(np.sqrt(mu * (2.0 / r_c - 1.0 / a_t)))
    v_phase_at_r_km_s  = float(np.sqrt(mu * (2.0 / r_c - 1.0 / a_phase)))
    dv1_km_s = v_phase_at_r_km_s - v_chaser_circ_km_s   # signed (km/s)
    # 6. Burn 1: tangential at chaser velocity direction
    v_vec = np.asarray(chaser_state_eci[3:6], dtype=float)
    v_hat = v_vec / np.linalg.norm(v_vec)
    dv1_vec_km_s = dv1_km_s * v_hat
    chaser_post_burn1 = chaser_state_eci.copy()
    chaser_post_burn1[3:6] += dv1_vec_km_s
    # 7. Drift k orbits in phasing ellipse
    drift_time = k * T_phase
    chaser_drifted = propagate_orbit(
        chaser_post_burn1, np.array([0.0, drift_time]),
        mu=mu, include_j2=False,
    )[-1]
    target_drifted = propagate_orbit(
        target_state_eci, np.array([0.0, drift_time]),
        mu=mu, include_j2=False,
    )[-1]
    # 8. Burn 2: re-circularise (oppositely-signed tangential)
    v_vec_2 = chaser_drifted[3:6]
    v_hat_2 = v_vec_2 / np.linalg.norm(v_vec_2)
    dv2_km_s = -dv1_km_s    # exact opposite (same magnitude, opposite sense)
    dv2_vec_km_s = dv2_km_s * v_hat_2
    chaser_final = chaser_drifted.copy()
    chaser_final[3:6] += dv2_vec_km_s
    # 9. Finite-burn corrections (Vallado Eq. 6-79)
    thrust_accel_m_s2 = thrust_acceleration * 1000.0
    v_circ_km_s = float(np.sqrt(mu / r_c))
    dv1_corr_m_s = finite_burn_corrected_dv(
        abs(dv1_km_s) * 1000.0, thrust_accel_m_s2, v_circ_km_s,
    )
    dv2_corr_m_s = finite_burn_corrected_dv(
        abs(dv2_km_s) * 1000.0, thrust_accel_m_s2, v_circ_km_s,
    )
    dv1_corr_km_s = dv1_corr_m_s / 1000.0
    dv2_corr_km_s = dv2_corr_m_s / 1000.0
    # 10. Burn durations
    dur1 = abs(dv1_corr_km_s) / thrust_acceleration
    dur2 = abs(dv2_corr_km_s) / thrust_acceleration
    burn1 = ImpulseEvent(
        epoch=0.0,
        dv_eci=dv1_vec_km_s,
        dv_magnitude_impulsive=abs(dv1_km_s),
        dv_magnitude_corrected=abs(dv1_corr_km_s),
        duration=dur1,
        label='phasing_drop' if dv1_km_s < 0 else 'phasing_raise',
    )
    burn2 = ImpulseEvent(
        epoch=drift_time,
        dv_eci=dv2_vec_km_s,
        dv_magnitude_impulsive=abs(dv2_km_s),
        dv_magnitude_corrected=abs(dv2_corr_km_s),
        duration=dur2,
        label='phasing_recirc',
    )
    rel_distance_m = float(np.linalg.norm(chaser_final[:3] - target_drifted[:3]) * 1000.0)
    return PhasingDriftPlan(
        burns=[burn1, burn2],
        drift_time=drift_time,
        n_phase_orbits=k,
        delta_theta_initial_deg=dtheta_deg,
        chaser_final_eci=chaser_final,
        target_final_eci=target_drifted,
        relative_distance_final_m=rel_distance_m,
    )
