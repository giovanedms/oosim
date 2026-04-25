"""SpaceX Crew Dragon Demo-2 (Endeavour) — first crewed commercial flight (May 2020).

Behnken and Hurley docked Crew Dragon Endeavour to ISS Harmony forward (IDA-2)
on 31 May 2020 after a ~19-hour autonomous rendezvous. First crewed flight from
US soil since the Space Shuttle retirement in 2011.

References:
    NASA Demo-2 mission page: https://www.nasa.gov/specials/dm2/
    NASA Commercial Crew blog: https://blogs.nasa.gov/commercialcrew/
    Lewis, J. L. & Donahoe, S. R. (2022). Standardization of In-Space and Surface
        Docking Systems. J. Space Safety Eng. 9(3). NTRS 20220004016.
"""
from .soyuz_ms17 import Burn, MissionRef


CREW_DRAGON_DM2 = MissionRef(
    mission_id="CREW_DRAGON_DM2",
    launch_utc="2020-05-30T19:22:45Z",
    dock_utc="2020-05-31T14:27:00Z",         # hard dock
    launch_to_dock_min=19.07 * 60,
    profile_orbits=12,
    burns=(
        Burn("INSERT", 0.0, 0.0, "Falcon 9 second-stage orbital insertion"),
        Burn("PHASING", 0.0, 0.0, "Multiple phasing burns over ~19 h (per-burn not public)"),
        Burn("HOLD_220M", 0.0, 0.0, "Hold @ 220 m for systems checkout"),
        Burn("HOLD_30M", 0.0, 0.0, "Hold @ 30 m for AI verification"),
        Burn("DOCK", 0.0, 0.0, "Soft + hard dock at IDA-2 (Harmony fwd)"),
    ),
    total_dv_ms=0.0,
    target_port="ISS Harmony forward IDA-2 (NDS soft-capture)",
    gnc_system="DragonEye thermal LIDAR + visible cameras + GPS",
    capture_mechanism="NASA Docking System (NDS) Block 1 / IDSS-compliant",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://www.nasa.gov/specials/dm2/",
    notes=(
        "First crewed commercial spaceflight from US soil. Crew: Behnken (Cmdr), "
        "Hurley (Pilot). Dragon Endeavour reused on Crew-2 (2021) and Crew-6 (2023). "
        "Per-burn dv not publicly released by SpaceX/NASA."
    ),
)
