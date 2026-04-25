"""Apollo-Soyuz Test Project (ASTP) — first international docking (July 1975).

The first international crewed spaceflight: NASA Apollo Command/Service Module
(CSM-111 + Docking Module) and Soviet Soyuz 19, launched 7.5 hours apart on
15 July 1975, performed two dockings using the new androgynous APAS-75 mechanism
designed jointly by Rockwell and RKK Energia. Total docked time: 44 hours.

References (validated):
    NASA TM-X-74149 / JSC-10607 (Dec 1975) — Apollo-Soyuz Mission Evaluation Report.
        NTRS 19760023154
    Ezell, E. C. & Ezell, L. N. (1978). The Partnership: A History of the Apollo-Soyuz
        Test Project. NASA SP-4209. https://history.nasa.gov/SP-4209/cover.htm
    Swan, W. L. (1976). Apollo-Soyuz Test Project Docking System. NTRS 19760021187.
"""
from .soyuz_ms17 import Burn, MissionRef


ASTP = MissionRef(
    mission_id="ASTP",
    launch_utc="1975-07-15T19:50:00Z",         # Apollo CSM launch (Soyuz 19 launched 7.5 h before)
    dock_utc="1975-07-17T16:09:00Z",            # Apollo active docking with Soyuz
    launch_to_dock_min=44.32 * 60,              # ~44 h after Apollo launch
    profile_orbits=29,
    burns=(
        Burn("PHASING", 0.0, 0.0, "Multiple Apollo phasing burns over 44 h"),
        Burn("NSR", 0.0, 0.0, "NSR (coelliptic Initiation) burn"),
        Burn("CORRECTIVE", 0.0, 0.0, "Mid-course corrections"),
        Burn("BRAKING", 0.0, 28.0, "Terminal braking gates 6000/3000/1500/450/30 m"),
    ),
    total_dv_ms=28.0,                            # rendezvous-phase only; ~28 m/s total
    target_port="Soyuz 19 docking module (APAS-75 androgynous)",
    gnc_system="PGNCS Apollo (no Rendezvous Radar — VHF ranging + sextant) + Soyuz Igla off",
    capture_mechanism="APAS-75 androgynous (Rockwell + RKK Energia, 3-fold petals + soft-capture latches)",
    granularity="HIGH",
    primary_doi="",
    primary_url="https://ntrs.nasa.gov/citations/19760023154",
    notes=(
        "First international crewed docking. Two dockings performed (Apollo active "
        "first, then Soyuz active for the second). 44 h total docked time. Docking "
        "module mass 2,012 kg; Apollo CSM-111 14,768 kg launch; Soyuz 19 ~6,790 kg."
    ),
)
