"""Cygnus NG-21 (2024) — Northrop Grumman Cygnus berthing to ISS via Canadarm2.

Mission profile (Tier B — reverse-engineered Δv placeholder):
  - Vehicle: Cygnus NG-21 (enhanced Cygnus with pressurized cargo module)
  - Launcher: Falcon 9, Cape Canaveral SLC-40
  - Launch:   2024-08-04
  - Berthing: 2024-08-06 (~2-day free-flight phase)
  - Capture:  Canadarm2 grapple at ISS Unity Node 1 nadir port
  - Wet mass at insertion: ~7,700 kg
  - Main engine: BT-4, nominal thrust 450 N
  - Thrust acceleration: 450 / 7700 ≈ 5.8e-5 km/s²
  - ISS altitude (epoch NG-21): ~420 km circular
  - ISS inclination: 51.6°
  - Reverse-engineered Δv: ~120 m/s (placeholder — TBR with NASA/NG primary docs)

Tier B classification: launch + berthing dates public; burn-by-burn breakdown
not available in open literature. Canadarm2 berthing (not docking) means
terminal tolerance is looser (capture envelope ~10 m on V-bar).
"""
import numpy as np

from oosim.validation.types import MissionScenario, ValidationTier

R_EARTH = 6378.137   # km
MU_EARTH = 398600.4418  # km³/s²

# Cygnus NG-21: BT-4 engine 450 N, wet mass ~7700 kg at insertion
# thrust_acceleration = 450 N / 7700 kg = 0.0584 m/s² = 5.84e-5 km/s²
NG21_THRUST_ACCEL = 5.8e-5  # km/s²

# Inertia rough estimate — Cygnus enhanced, scaled from Soyuz by mass ratio
NG21_INERTIA = np.diag([4500.0, 4600.0, 1500.0])  # kg·m²


def make_cygnus_ng21_scenario() -> MissionScenario:
    """Build the Cygnus NG-21 reproduction scenario with placeholder initial conditions.

    Canadarm2-capture berthing style: terminal target is the capture envelope
    (~10 m behind ISS on V-bar, i.e. -10 m in LVLH y), not a hard-dock port.
    When NASA/Northrop primary trajectory docs become available, replace the
    geometric placeholders with insertion-state vectors from official data.
    """
    # --- ISS state at NG-21 epoch (420 km circular, 51.6° inclination) ---
    iss_alt = 420.0
    a_iss = R_EARTH + iss_alt
    v_iss = float(np.sqrt(MU_EARTH / a_iss))
    inc = np.radians(51.6)
    nu_iss = 0.0
    Rx = np.array([
        [1, 0,            0           ],
        [0, np.cos(inc), -np.sin(inc) ],
        [0, np.sin(inc),  np.cos(inc) ],
    ])
    r_iss = a_iss * np.array([np.cos(nu_iss), np.sin(nu_iss), 0.0])
    v_iss_v = v_iss * np.array([-np.sin(nu_iss), np.cos(nu_iss), 0.0])
    iss_state = np.concatenate([Rx @ r_iss, Rx @ v_iss_v])

    # --- Cygnus NG-21 post-insertion state (230 km circular, ~4° behind ISS) ---
    cygnus_alt = 230.0
    a_cygnus = R_EARTH + cygnus_alt
    v_cygnus = float(np.sqrt(MU_EARTH / a_cygnus))
    nu_cygnus = np.radians(-4.0)  # ~4° behind ISS (placeholder)
    r_cygnus = a_cygnus * np.array([np.cos(nu_cygnus), np.sin(nu_cygnus), 0.0])
    v_cygnus_v = v_cygnus * np.array([-np.sin(nu_cygnus), np.cos(nu_cygnus), 0.0])
    cygnus_state = np.concatenate([Rx @ r_cygnus, Rx @ v_cygnus_v])

    return MissionScenario(
        name="Cygnus NG-21",
        year=2024,
        chaser_initial_eci=cygnus_state,
        target_initial_eci=iss_state,
        expected_dv_total_m_s=120.0,          # reverse-engineered placeholder (Tier B)
        expected_duration_min=250.0,          # pipeline simulates ~4 h; real free-flight ~2 days
        tier=ValidationTier.TIER_B,
        inertia=NG21_INERTIA,
        thrust_acceleration=NG21_THRUST_ACCEL,
        n_phase_orbits=2,
        t_terminal=400.0,
        target_pos_lvlh_m=np.array([0., -10., 0.]),     # berthing capture envelope
        corridor_entry_lvlh_m=np.array([0., -50., 0.]), # default corridor entry
        corridor_entry_time_s=600.0,                    # M9 transfer duration default
        references=[
            "NASA Press Kit: Cygnus NG-21 (August 2024), "
            "https://www.nasa.gov/press-kit/cygnus-ng-21",
            "Northrop Grumman Cygnus spacecraft product page, "
            "https://www.northropgrumman.com/space/cygnus-spacecraft",
            "Foust, J. (2024) SpaceNews: Cygnus NG-21 berthing at ISS, Aug 2024.",
        ],
        notes=(
            "Canadarm2 berthing (not autonomous docking); terminal tolerance "
            "is the Canadarm2 capture envelope (~10 m on V-bar). "
            "Placeholder initial conditions — Tier B reverse-engineered Δv 120 m/s "
            "pending NASA/Northrop primary trajectory docs."
        ),
    )
