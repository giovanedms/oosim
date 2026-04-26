"""Astroscale ELSA-d — first commercial magnetic-capture debris demonstration (2021-24).

The End-of-Life Service by Astroscale demonstration (ELSA-d) launched March 2021
with two pre-mated spacecraft: a 175 kg Servicer and a 17 kg Client featuring a
magnetic docking plate. The mission demonstrated first-ever magnetic capture in
orbit on 25 August 2021. A subsequent thruster anomaly (May 2022, lost 4 of 8
ECAPS thrusters) prevented the originally planned more-complex tumbling-target
captures, but the team continued to demonstrate close-approach operations until
deorbit on 24 January 2024.

References:
    Forshaw, J. et al. (2021). ELSA-d: A Case Study of ADR Mission Operational
        Practice. 72nd International Astronautical Congress (IAC),
        IAC-21,A6,10-B6.5,1,x64392
    Astroscale press kit and mission updates 2021-2024.
"""
from .soyuz_ms17 import Burn, MissionRef


ELSAD = MissionRef(
    mission_id="ELSAD",
    launch_utc="2021-03-22T06:07:00Z",
    dock_utc="2021-08-25T00:00:00Z",          # 1st magnetic capture
    launch_to_dock_min=156.0 * 24 * 60,        # ~156 days
    profile_orbits=2400,
    burns=(
        Burn("INSERT", 0.0, 0.0, "Soyuz-2.1a orbital insertion (Baikonur)"),
        Burn("CHECKOUT", 0.0, 0.0, "Spacecraft checkout 22 Mar -- 24 Aug 2021"),
        Burn("CAPTURE1", 0.0, 0.0, "First magnetic capture demo (25 Aug 2021)"),
        Burn("ANOMALY", 0.0, 0.0, "Thruster anomaly May 2022 (lost 4/8 ECAPS)"),
        Burn("FINAL", 0.0, 0.0, "Close-approach 159 m (7 Apr 2022, post-anomaly)"),
    ),
    total_dv_ms=0.0,
    target_port="ELSA-d Client (175 kg Servicer captures 17 kg Client via magnetic plate)",
    gnc_system="Visible camera + nav sensor + autonomous FDIR + collision avoidance",
    capture_mechanism="Magnetic capture system + docking plate (Astroscale proprietary)",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://www.astroscale.com/en/missions/elsa-d/",
    notes=(
        "First commercial magnetic capture in orbit (25 Aug 2021). Pre-mated "
        "Servicer+Client pair launched together. May 2022 thruster anomaly "
        "(4/8 ECAPS lost) limited subsequent captures. Demonstrated 159 m "
        "approach with reduced propulsion (7 Apr 2022). Deorbit 24 Jan 2024 "
        "after ~2.85 years on-orbit. Foundational for the subsequent ADRAS-J "
        "mission (2024) which targeted a real space-debris H-IIA upper stage."
    ),
)
