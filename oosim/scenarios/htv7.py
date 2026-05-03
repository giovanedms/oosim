"""HTV-7 Kounotori 7 (2018) — JAXA berthing to ISS via Canadarm2 capture.

Reference:
  - JAXA HTV-7 mission page:
    https://www.jaxa.jp/projects/rockets/htv/index_e.html
  - Inamori et al. (2018) HTV-7 operations overview (JAXA report)

Mission profile (reverse-engineered Tier B — no public burn-by-burn breakdown):
  - Launched: 2018-09-22 from Tanegashima Space Center
  - Canadarm2 capture: 2018-09-27 (~5 days free-flight)
  - Target: ISS Common Berthing Mechanism (Node-2 nadir or zenith port)
  - ISS altitude at capture epoch: ~400 km
  - Wet mass at insertion: ~16,500 kg
  - Berthing (not docking): HTV held at ~10 m on V-bar then grappled by Canadarm2
  - Δv budget reverse-engineered estimate: ~150 m/s
    (full mission Δv included phasing over 5 days NOT simulated here;
    we simulate only the orbital insertion → capture envelope approach)

Tier B classification: published mass + approximate ΔH but burn-by-burn
breakdown not available in open literature.
"""
import numpy as np

from oosim.validation.types import MissionScenario, ValidationTier

R_EARTH = 6378.137      # km
MU_EARTH = 398600.4418  # km³/s²

# HTV-7 wet mass at insertion ~16,500 kg; 4 × HBT-5 490 N = 1960 N
# Thrust acceleration = 1960 N / 16500 kg = 0.119 m/s² = 1.19e-4 km/s²
HTV7_THRUST_ACCEL = 1.19e-4  # km/s²

# Inertia: rough estimate scaled from Soyuz (7000 kg) by mass ratio 16500/7000 ≈ 2.36
HTV7_INERTIA = np.diag([9000.0, 9200.0, 3000.0])  # kg·m²


def make_htv7_scenario() -> MissionScenario:
    """Build the HTV-7 Kounotori 7 reproduction scenario.

    Uses placeholder initial conditions (geometric construction) for ISS and
    HTV-7 post-insertion states. Replace with official trajectory vectors when
    JAXA primary documentation becomes available.

    Returns
    -------
    MissionScenario
        Fully populated Tier-B scenario for the F3-real validation pipeline.
    """
    # Placeholder ISS state at HTV-7 capture epoch (400 km circular, 51.6°)
    iss_alt = 400.0
    a_iss = R_EARTH + iss_alt
    v_iss = float(np.sqrt(MU_EARTH / a_iss))
    inc = np.radians(51.6)
    nu_iss = 0.0

    # Rotation matrix for 51.6° inclination (rotation about X-axis)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(inc), -np.sin(inc)],
        [0, np.sin(inc), np.cos(inc)],
    ])

    r_iss = a_iss * np.array([np.cos(nu_iss), np.sin(nu_iss), 0.0])
    v_iss_v = v_iss * np.array([-np.sin(nu_iss), np.cos(nu_iss), 0.0])
    iss_state = np.concatenate([Rx @ r_iss, Rx @ v_iss_v])

    # Placeholder HTV-7 post-insertion state (250 km circular, ~5° behind ISS)
    htv_alt = 250.0
    a_htv = R_EARTH + htv_alt
    v_htv = float(np.sqrt(MU_EARTH / a_htv))
    nu_htv = np.radians(-5.0)  # ~5° behind ISS on same orbital plane

    r_htv = a_htv * np.array([np.cos(nu_htv), np.sin(nu_htv), 0.0])
    v_htv_v = v_htv * np.array([-np.sin(nu_htv), np.cos(nu_htv), 0.0])
    htv_state = np.concatenate([Rx @ r_htv, Rx @ v_htv_v])

    return MissionScenario(
        name="HTV-7 Kounotori 7",
        year=2018,
        chaser_initial_eci=htv_state,
        target_initial_eci=iss_state,
        expected_dv_total_m_s=150.0,       # reverse-engineered Tier B placeholder
        expected_duration_min=250.0,       # pipeline simulates M5+M8+M9+M6 only (~4 h)
        tier=ValidationTier.TIER_B,
        inertia=HTV7_INERTIA,
        thrust_acceleration=HTV7_THRUST_ACCEL,
        n_phase_orbits=2,
        t_terminal=400.0,
        target_pos_lvlh_m=np.array([0., -10., 0.]),    # Canadarm2 capture envelope center
        corridor_entry_lvlh_m=np.array([0., -50., 0.]),  # default corridor entry
        corridor_entry_time_s=600.0,
        references=[
            "JAXA HTV-7 mission page: https://www.jaxa.jp/projects/rockets/htv/index_e.html",
            "JAXA HTV overview: https://iss.jaxa.jp/en/htv/",
            "HTV-7 Kounotori 7 press kit (JAXA, 2018)",
        ],
        notes=(
            "Berthing (not docking): HTV-7 was grappled by Canadarm2 at ~10 m on V-bar. "
            "Placeholder initial conditions; real 5-day free-flight phasing NOT modelled. "
            "Only the rendezvous final approach is simulated via M5+M8+M9+M6. Tier B."
        ),
    )
