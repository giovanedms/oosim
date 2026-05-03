"""ATV-1 Jules Verne (2008) — first European automated docking to ISS.

Reference: Baize et al. (2008) AIAA SpaceOps, DOI 10.2514/6.2008-3537.

Mission profile (placeholder values — TBR with ESA primary docs):
  - Launched: 2008-03-09 from Kourou
  - Docked: 2008-04-03 (24-day free-flight phase)
  - Target: ISS Service Module aft port (Zvezda)
  - ISS altitude at docking: ~340 km (much lower than current ~420 km)
  - Wet mass at insertion: ~20.7 t (largest cargo vehicle to ISS at the time)
  - Δv budget reverse-engineered estimate: ~120 m/s for the rendezvous
    (full mission Δv was much higher including phasing waits over 24 days
    that we DON'T simulate; we simulate just the orbital insertion → docking
    Δv consumed for orbit raising and final approach)

Tier B classification: published mass + ΔH but burn-by-burn breakdown
not in open literature.
"""
import numpy as np

from oosim.validation.types import MissionScenario, ValidationTier

R_EARTH = 6378.137  # km
MU_EARTH = 398600.4418

# ATV-1 mass at insertion ~20,700 kg; main engine thrust 4 × 490 N = 1960 N
# Thrust acceleration ~9.5e-5 km/s² (slightly higher than Soyuz)
ATV1_THRUST_ACCEL = 9.5e-5
# Inertia (very rough, scaled from Soyuz by mass ratio)
ATV1_INERTIA = np.diag([12000.0, 12200.0, 4000.0])  # kg·m²


def make_atv1_scenario() -> MissionScenario:
    """Build the ATV-1 reproduction scenario with placeholder initial conditions.

    When ESA primary docs become available, replace the geometric placeholders
    with insertion-state vectors derived from official trajectory data.
    """
    # Placeholder ISS state at ATV-1 docking epoch (340 km circular, 51.6°)
    iss_alt = 340.0
    a_iss = R_EARTH + iss_alt
    v_iss = float(np.sqrt(MU_EARTH / a_iss))
    inc = np.radians(51.6)
    nu_iss = 0.0
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(inc), -np.sin(inc)],
        [0, np.sin(inc), np.cos(inc)],
    ])
    r_iss = a_iss * np.array([np.cos(nu_iss), np.sin(nu_iss), 0.0])
    v_iss_v = v_iss * np.array([-np.sin(nu_iss), np.cos(nu_iss), 0.0])
    iss_state = np.concatenate([Rx @ r_iss, Rx @ v_iss_v])
    # Placeholder ATV-1 post-insertion state (260 km circular, ~3° behind ISS)
    atv_alt = 260.0
    a_atv = R_EARTH + atv_alt
    v_atv = float(np.sqrt(MU_EARTH / a_atv))
    nu_atv = np.radians(-3.0)
    r_atv = a_atv * np.array([np.cos(nu_atv), np.sin(nu_atv), 0.0])
    v_atv_v = v_atv * np.array([-np.sin(nu_atv), np.cos(nu_atv), 0.0])
    atv_state = np.concatenate([Rx @ r_atv, Rx @ v_atv_v])
    return MissionScenario(
        name="ATV-1 Jules Verne",
        year=2008,
        chaser_initial_eci=atv_state,
        target_initial_eci=iss_state,
        expected_dv_total_m_s=120.0,         # reverse-engineered placeholder
        expected_duration_min=240.0,         # placeholder; real free-flight was 24 days
        tier=ValidationTier.TIER_B,
        inertia=ATV1_INERTIA,
        thrust_acceleration=ATV1_THRUST_ACCEL,
        n_phase_orbits=2,
        t_terminal=400.0,
        target_pos_lvlh_m=np.array([0., -15.0, 0.]),    # ATV approach corridor
        references=[
            "Baize et al. (2008) AIAA SpaceOps, DOI 10.2514/6.2008-3537",
            "ESA mission page: https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/ATV",
        ],
        notes=(
            "Placeholder initial conditions; real mission used 24-day phasing "
            "with multiple hold points not modelled in F3-real M9. Tier B."
        ),
    )
