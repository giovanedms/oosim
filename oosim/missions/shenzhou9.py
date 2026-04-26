"""Shenzhou-9 — first Chinese crewed docking (June 2012).

Shenzhou-9 was the first Chinese crewed mission to perform a docking, both
automated (with Tiangong-1) and manual (the second docking, piloted by Liu
Wang on 24 June 2012). Crew included Liu Yang, the first Chinese woman in
space.

References (validated DOIs):
    Xie, Y. et al. (2013). Accurate and Stable Control of Shenzhou Spacecraft
        in Rendezvous and Docking. IFAC Proc. Vol. 46(20).
        DOI: 10.3182/20130902-5-de-2040.00063
    Hu, J. et al. (2014). Shenzhou Spacecraft Rendezvous and Docking Manual
        Control System Design. Sci. Sin. Tech. 44.
        DOI: 10.1360/092013-1262
"""
from .soyuz_ms17 import Burn, MissionRef


SHENZHOU9 = MissionRef(
    mission_id="SHENZHOU9",
    launch_utc="2012-06-16T10:37:24Z",
    dock_utc="2012-06-18T06:07:00Z",          # automated dock
    launch_to_dock_min=43.5 * 60,
    profile_orbits=29,
    burns=(
        Burn("INSERT", 0.0, 0.0, "Long March 2F orbital insertion"),
        Burn("PHASING", 0.0, 0.0, "Phasing burns over ~44 h (per-burn not public)"),
        Burn("DOCK_AUTO", 0.0, 0.0, "Automated docking with Tiangong-1 (18 Jun)"),
        Burn("UNDOCK", 0.0, 0.0, "Undock for manual docking test (24 Jun)"),
        Burn("DOCK_MANUAL", 0.0, 0.0, "Manual docking by Liu Wang (24 Jun) — first Chinese crewed manual"),
    ),
    total_dv_ms=0.0,
    target_port="Tiangong-1 forward (APAS-derived androgynous, SAST Shanghai)",
    gnc_system="Laser/microwave radar + CCD optical + manual interface (TWS, HUD, hand controller)",
    capture_mechanism="APAS-derived androgynous (China Aerospace Science and Technology Corp)",
    granularity="MEDIUM",
    primary_doi="10.1360/092013-1262",
    primary_url="https://en.cmse.gov.cn/",
    notes=(
        "First Chinese crewed docking. Crew: Jing Haipeng (Cmdr), Liu Wang, "
        "Liu Yang (first Chinese woman in space). Two dockings: automated 18 Jun, "
        "manual 24 Jun (first Chinese manual). Mass ~8,130 kg."
    ),
)
