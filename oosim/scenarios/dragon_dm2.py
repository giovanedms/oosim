"""Crew Dragon Demo-2 (DM-2) — first crewed Commercial Crew mission to ISS (SpaceX, 2020).

References:
  - NASA Commercial Crew Program, DM-2 press kit:
    https://www.nasa.gov/commercialcrew/demo-mission-2
  - SpaceX Dragon DM-2 mission press kit (May 2020):
    https://www.spacex.com/vehicles/dragon/
  - NASA Johnson / NDS (NASA Docking System) IDA-2 interface:
    https://www.nasa.gov/feature/goddard/2019/the-international-docking-adapter

Mission profile (reverse-engineered Tier B — SpaceX does not publish burn-by-burn Δv):
  - Launched: 2020-05-30 from KSC LC-39A
  - Docked: 2020-05-31 (~19 h after launch — fast-rendezvous NDS docking to PMA-2/IDA-2)
  - Target port: PMA-2/IDA-2 on ISS forward port (Node 2)
  - ISS altitude at docking: ~420 km
  - Wet mass at insertion: ~12,500 kg (crew + cargo configuration)
  - Propulsion: 16 × Draco hypergolic thrusters (~400 N each); typical translation
    uses 1-2 pods (~3-4 thrusters ≈ 1200 N effective).
    Conservative single-axis thrust_accel: 1200/12500 = 0.096 m/s² ≈ 9.5e-5 km/s².
  - Reverse-engineered Δv: ~90 m/s (placeholder pending NASA CCiCap primary telemetry).

Tier B classification: total flight duration + ΔH publicly available; per-burn
breakdown not released.  expected_duration_min=230 covers the M5+M8+M9+M6 portion
of the approach (not the full 19 h free-flight).
"""
import numpy as np

from oosim.validation.types import MissionScenario, ValidationTier

R_EARTH = 6378.137      # km
MU_EARTH = 398600.4418  # km³/s²

# Crew Dragon wet mass at insertion ~12,500 kg.
# 16 × Draco thrusters rated ~400 N each; typical translation uses 1-2 pods
# (~3-4 thrusters = ~1200 N effective).  Conservative single-axis thrust_accel:
#   ~1200 N / 12500 kg = 0.096 m/s² ≈ 9.5e-5 km/s²
# (same order as ATV-1 value used for pipeline tuning).
DM2_THRUST_ACCEL = 9.5e-5  # km/s²

# Inertia (rough estimate, scaled from Soyuz by mass ratio ~12500/7150 ≈ 1.75)
DM2_INERTIA = np.diag([7000.0, 7100.0, 2400.0])  # kg·m²


def make_dragon_dm2_scenario() -> MissionScenario:
    """Build the Crew Dragon DM-2 reproduction scenario with placeholder initial conditions.

    When NASA Commercial Crew primary telemetry becomes available, replace the
    geometric placeholders with insertion-state vectors derived from official data.
    """
    # ISS state at DM-2 docking epoch (420 km circular, 51.6°)
    iss_alt = 420.0
    a_iss = R_EARTH + iss_alt
    v_iss = float(np.sqrt(MU_EARTH / a_iss))
    inc = np.radians(51.6)
    nu_iss = 0.0

    # Rotation matrix for 51.6° inclination (rotate equatorial plane by inc around x-axis)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(inc), -np.sin(inc)],
        [0, np.sin(inc),  np.cos(inc)],
    ])

    r_iss = a_iss * np.array([np.cos(nu_iss), np.sin(nu_iss), 0.0])
    v_iss_v = v_iss * np.array([-np.sin(nu_iss), np.cos(nu_iss), 0.0])
    iss_state = np.concatenate([Rx @ r_iss, Rx @ v_iss_v])

    # Placeholder Dragon post-insertion state (200 km circular, ~7° behind ISS)
    # Fast rendezvous profile; chaser starts lower to gain phase angle on ISS.
    dragon_alt = 200.0
    a_dragon = R_EARTH + dragon_alt
    v_dragon = float(np.sqrt(MU_EARTH / a_dragon))
    nu_dragon = np.radians(-7.0)   # ~7° behind ISS (representative fast-rendezvous)

    r_dragon = a_dragon * np.array([np.cos(nu_dragon), np.sin(nu_dragon), 0.0])
    v_dragon_v = v_dragon * np.array([-np.sin(nu_dragon), np.cos(nu_dragon), 0.0])
    dragon_state = np.concatenate([Rx @ r_dragon, Rx @ v_dragon_v])

    return MissionScenario(
        name="Crew Dragon Demo-2 (DM-2)",
        year=2020,
        chaser_initial_eci=dragon_state,
        target_initial_eci=iss_state,
        expected_dv_total_m_s=90.0,          # reverse-engineered placeholder (Tier B)
        expected_duration_min=230.0,          # M5+M8+M9+M6 slice; full flight was ~19 h
        tier=ValidationTier.TIER_B,
        inertia=DM2_INERTIA,
        thrust_acceleration=DM2_THRUST_ACCEL,
        n_phase_orbits=2,
        t_terminal=400.0,
        target_pos_lvlh_m=np.array([0., -10., 0.]),    # NDS docking envelope (IDA-2)
        corridor_entry_lvlh_m=np.array([0., -50., 0.]),
        corridor_entry_time_s=600.0,
        references=[
            "NASA Commercial Crew Program DM-2: https://www.nasa.gov/commercialcrew/demo-mission-2",
            "SpaceX Dragon vehicle page: https://www.spacex.com/vehicles/dragon/",
            "NASA IDA-2 NDS docking feature: https://www.nasa.gov/feature/goddard/2019/the-international-docking-adapter",
        ],
        notes=(
            "Reverse-engineered Tier B; SpaceX does not publish per-burn Δv breakdown. "
            "Insertion state is a geometric placeholder for 200 km circular / 7° phase offset "
            "representing the fast-rendezvous profile. NDS docking to PMA-2/IDA-2 forward port."
        ),
    )
