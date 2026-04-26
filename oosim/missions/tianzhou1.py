"""Tianzhou-1 — first Chinese cargo automated docking (April 2017).

China's first cargo spacecraft, Tianzhou-1 docked three times with Tiangong-2
during its ~5-month mission, including a 6.5-hour fast-rendezvous demonstration
on 12 September 2017 — analogous to (and slightly slower than) the Russian
Soyuz fast-rendezvous profiles.

References (validated DOIs):
    Lei, J. et al. (2023). Research and Development of the Tianzhou Cargo
        Spacecraft. Space: Sci. & Tech. (AAAS).
        DOI: 10.34133/space.0006
    Chen, C. et al. (2025). Tianzhou cargo spacecraft all-phase autonomous
        quick rendezvous and docking and in-orbit realization.
        IFAC-PapersOnLine. DOI: 10.1016/j.ifacol.2025.11.165
"""
from .soyuz_ms17 import Burn, MissionRef


TIANZHOU1 = MissionRef(
    mission_id="TIANZHOU1",
    launch_utc="2017-04-20T11:41:00Z",
    dock_utc="2017-04-22T04:16:00Z",          # 1st docking
    launch_to_dock_min=40.58 * 60,
    profile_orbits=27,
    burns=(
        Burn("INSERT", 0.0, 0.0, "Long March 7 orbital insertion (Wenchang)"),
        Burn("DOCK1", 0.0, 0.0, "1st docking (22 Apr) — propellant transfer test"),
        Burn("DOCK2", 0.0, 0.0, "2nd docking (15 Jun) — refueling test"),
        Burn("DOCK3_FAST", 0.0, 0.0, "3rd docking (12 Sep) — 6.5h fast-rendezvous demo"),
    ),
    total_dv_ms=0.0,
    target_port="Tiangong-2 (multiple ports across 3 dockings)",
    gnc_system="Microwave radar + LIDAR + optical CCD (Chinese-built)",
    capture_mechanism="Chinese androgynous (heritage APAS-89/95 derived)",
    granularity="MEDIUM-HIGH",
    primary_doi="10.34133/space.0006",
    primary_url="https://en.cmse.gov.cn/",
    notes=(
        "First Chinese cargo automated docking. Three dockings demonstrated. "
        "Mass ~13,000 kg launch / ~6,500 kg cargo capacity. The 3rd docking "
        "(Sep 2017) was a 6.5h fast-rendezvous, slower than Soyuz MS-17's "
        "3.06h ultra-rapid (2020) but pioneering for Chinese cargo ops."
    ),
)
