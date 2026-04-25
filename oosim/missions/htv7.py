"""HTV-7 Kounotori — JAXA H-II Transfer Vehicle 7 (September 2018).

HTV-7 was the seventh JAXA cargo vehicle to berth with the ISS via Canadarm2,
following the standard PROX-based approach with hold points at AI (5 km),
500 m, 250 m, 30 m, and the 10 m capture box. First HTV with the HSRC
(HTV Small Re-entry Capsule) for sample return.

Reference (validated DOI):
    Ueda, S., Kasai, T., Uematsu, H. (2010). HTV Rendezvous Technique and GN&C
        Design Evaluation. AIAA. DOI: 10.2514/6.2010-7664
        (covers HTV architecture, common to HTV-1 through HTV-9)
    Matsumoto, T. (2003). PROX system development. AIAA. DOI: 10.2514/6.2003-2282
"""
from .soyuz_ms17 import Burn, MissionRef


HTV7_KOUNOTORI = MissionRef(
    mission_id="HTV7_KOUNOTORI",
    launch_utc="2018-09-22T17:52:27Z",
    dock_utc="2018-09-27T16:08:00Z",          # berthing complete
    launch_to_dock_min=118.27 * 60,            # ~4.9 days
    profile_orbits=78,                          # ~5 days x 15.5 orb/day
    burns=(
        Burn("PHASING_AI", 0.0, 0.0, "Multiple phasing burns over 5 days"),
        Burn("AI_5KM", 0.0, 0.0, "Approach Initiation hold @ 5 km below ISS"),
        Burn("HOLD_500M", 0.0, 0.0, "Hold @ 500 m"),
        Burn("HOLD_250M", 0.0, 0.0, "Hold @ 250 m, AI checkout"),
        Burn("HOLD_30M", 0.0, 0.0, "Hold @ 30 m"),
        Burn("CAPTURE_10M", 0.0, 0.0, "Free-drift in 10 m capture box for SSRMS"),
    ),
    total_dv_ms=0.0,                            # NOT PUBLISHED per-burn
    target_port="ISS Harmony nadir CBM via Canadarm2",
    gnc_system="PROX + RGPS + RVS LIDAR (rendezvous sensor) + GPSR",
    capture_mechanism="Canadarm2 SSRMS capture + Common Berthing Mechanism (passive)",
    granularity="HIGH",
    primary_doi="10.2514/6.2010-7664",
    primary_url="https://iss.jaxa.jp/en/htv/mission/htv-7/",
    notes=(
        "First HTV with HSRC (return capsule). Total mass ~16,500 kg. "
        "Cargo ~6,200 kg (4,300 PLC + 1,900 ULC). Berthing nominal — no anomalies."
    ),
)
