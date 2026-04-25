"""Cargo Dragon-2 CRS-21 — first US autonomous cargo docking (December 2020).

The 21st SpaceX commercial resupply mission (and the first using Cargo Dragon-2,
the upgraded autonomous-docking variant of the original berthing-only Dragon-1)
docked autonomously to ISS Harmony zenith (IDA-3) on 7 December 2020. First
operational use of IDA-3.

References:
    NASA CRS-21 blog: https://blogs.nasa.gov/spacexcrs21/
    eoPortal Dragon-2: https://www.eoportal.org/satellite-missions/iss-spacex-crs-21
"""
from .soyuz_ms17 import Burn, MissionRef


CARGO_DRAGON_CRS21 = MissionRef(
    mission_id="CARGO_DRAGON_CRS21",
    launch_utc="2020-12-06T16:17:08Z",
    dock_utc="2020-12-07T18:40:00Z",
    launch_to_dock_min=26.38 * 60,
    profile_orbits=17,
    burns=(
        Burn("INSERT", 0.0, 0.0, "Falcon 9 second-stage orbital insertion"),
        Burn("PHASING", 0.0, 0.0, "Phasing burns over ~26 h"),
        Burn("APPROACH", 0.0, 0.0, "Final approach to IDA-3 hold points"),
        Burn("DOCK", 0.0, 0.0, "Autonomous NDS soft + hard dock"),
    ),
    total_dv_ms=0.0,
    target_port="ISS Harmony zenith IDA-3 (NDS, first operational use)",
    gnc_system="DragonEye LIDAR + cameras + GPS (same stack as Crew Dragon)",
    capture_mechanism="NASA Docking System (NDS) Block 1",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://blogs.nasa.gov/spacexcrs21/",
    notes=(
        "First US cargo automated docking (Dragon-1 was berthing only via Canadarm2). "
        "First IDA-3 use. ~2,972 kg cargo up; ~2,000 kg down at splashdown."
    ),
)
