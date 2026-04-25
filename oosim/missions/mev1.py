"""Northrop Grumman MEV-1 + Intelsat 901 — first commercial servicing (Feb 2020).

The Mission Extension Vehicle 1 (MEV-1), built by Northrop Grumman SpaceLogistics,
docked with Intelsat 901 (a defunct satellite in graveyard orbit ~290 km above
GEO) using a proprietary mechanical capture of the satellite's apogee engine
nozzle. The pair were then maneuvered back to operational geostationary
orbit, where MEV-1 acted as a propulsion-and-attitude module for IS-901,
extending its operational life by 5 years before undocking in April 2025.

This is the FIRST commercial on-orbit servicing mission of any kind in history.

References (no Crossref-validated DOI; Northrop/Intelsat press releases primary):
    https://news.northropgrumman.com/news/releases/northrop-grumman-successfully-completes-historic-first-docking-of-mission-extension-vehicle-with-intelsat-901-satellite
    https://www.intelsat.com/resources/blog/mev-1-a-look-back-at-intelsats-groundbreaking-journey/
    https://news.northropgrumman.com/satellites/Northrop-Grumman-Achieves-First-Ever-Undocking-Between-Two-Commercial-Spacecraft-in-Geosynchronous-Orbit
"""
from .soyuz_ms17 import Burn, MissionRef


MEV1_INTELSAT901 = MissionRef(
    mission_id="MEV1_INTELSAT901",
    launch_utc="2019-10-09T10:17:00Z",         # Proton-M, Baikonur, rideshare
    dock_utc="2020-02-25T07:15:00Z",           # graveyard orbit ~290 km above GEO
    launch_to_dock_min=138.0 * 24 * 60,        # 138 days = ~3,312 h = ~198,720 min
    profile_orbits=140,                         # GEO drift orbit, ~1 orbit/day
    burns=(
        Burn("INSERT", 0.0, 0.0, "GTO insertion via Proton-M"),
        Burn("CIRC", 0.0, 0.0, "Circularization to GEO drift"),
        Burn("PHASING", 0.0, 0.0, "Multi-month low-thrust phasing using Hall-effect xenon EP"),
        Burn("APPROACH", 0.0, 0.0, "Final approach to IS-901 in graveyard orbit"),
        Burn("DOCK", 0.0, 0.0, "Mechanical capture of IS-901 LAE nozzle"),
    ),
    total_dv_ms=0.0,
    target_port="Intelsat 901 LAE (Liquid Apogee Engine) nozzle",
    gnc_system="Proprietary SpaceLogistics GNC + Hall-effect xenon EP main propulsion",
    capture_mechanism="Mechanical capture of LAE nozzle (proprietary) — no docking adapter on target",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://news.northropgrumman.com/news/releases/northrop-grumman-successfully-completes-historic-first-docking-of-mission-extension-vehicle-with-intelsat-901-satellite",
    notes=(
        "First commercial servicing in history. Critically, IS-901 was NOT designed "
        "to be serviced — MEV-1 captured the LAE nozzle, a feature retroactively "
        "exploited as a docking interface. Undocked April 2025 after 5-year "
        "service contract. MEV-1 mass ~2,330 kg; IS-901 launch mass 4,723 kg "
        "(SS/Loral 1300 bus). Hall-effect EP provides >=15 years operational life."
    ),
)
