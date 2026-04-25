"""Cygnus NG-21 (S.S. Francis R. "Dick" Scobee) berthing — August 2024.

The 21st operational Cygnus mission, notable as the first Cygnus launched on
a SpaceX Falcon 9 (after the retirement of the Antares 230+) and reportedly
celebrated as the "50th cosmic catch" of Canadarm2 — a claim repeated in
secondary sources but not validated in primary NASA/CSA communications.

References:
    NASA Northrop Grumman 21st CRS mission overview:
        https://www.nasa.gov/general/overview-for-nasas-northrop-grumman-21st-commercial-resupply-mission/
    NASA News Release:
        https://www.nasa.gov/news-release/nasa-sets-coverage-for-northrop-grummans-21st-station-resupply-launch/
    Northrop press:
        https://news.northropgrumman.com/cygnus/northrop-grummans-ng-21-resupply-mission-successfully-launches-to-the-international-space-station

Per-burn delta-v not in open NASA/Northrop documentation.
"""
from .soyuz_ms17 import Burn, MissionRef


CYGNUS_NG21 = MissionRef(
    mission_id="CYGNUS_NG21",
    launch_utc="2024-08-04T15:02:00Z",        # Falcon 9, SLC-40 Cape Canaveral
    dock_utc="2024-08-06T07:11:00Z",          # Canadarm2 capture by Matthew Dominick
    launch_to_dock_min=40.15 * 60,             # ~40 h
    profile_orbits=27,                         # ~40h × ~16 orb/day
    burns=(
        Burn("PHASING", 0.0, 0.0, "Multiple phasing burns over 40 h (per-burn not public)"),
        Burn("HOLD_AI", 0.0, 0.0, "Approach Initiation hold (~5 km below ISS)"),
        Burn("HOLD_500M", 0.0, 0.0, "Hold @ 500 m"),
        Burn("HOLD_30M", 0.0, 0.0, "Hold @ 30 m"),
        Burn("CAPTURE_10M", 0.0, 0.0, "Free-drift in 10 m capture box for SSRMS"),
    ),
    total_dv_ms=0.0,
    target_port="ISS Unity Earth-facing (nadir) CBM via Canadarm2",
    gnc_system="TriDAR + LIDAR + cameras",
    capture_mechanism="Canadarm2 SSRMS capture + CBM (passive)",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://www.nasa.gov/general/overview-for-nasas-northrop-grumman-21st-commercial-resupply-mission/",
    notes=(
        "First Cygnus on Falcon 9 (post Antares 230+ retirement). 3,720 kg cargo. "
        "Reported as '50th cosmic catch' of Canadarm2 (claim 🟡 — not validated "
        "in primary NASA/CSA communications, retained for context only)."
    ),
)
