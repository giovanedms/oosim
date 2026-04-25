"""STS-71 Atlantis / Mir — first Shuttle-Mir docking (June 1995).

The first Shuttle docking with the Russian Mir space station, beginning the
Phase-1 ISS preparatory program. Atlantis used the Russian APAS-89 docking
mechanism mounted on the Orbiter Docking System (ODS) in the payload bay.
R-bar approach from below at ~0.033 m/s closing rate.

References (validated DOIs):
    Goodman, J. L. (2006). History of Space Shuttle Rendezvous and Proximity
        Operations. J. Spacecraft and Rockets 43(5):944-959. DOI: 10.2514/1.19653
    Frike, R. W. (1995). STS-71 Space Shuttle Mission Report. NSTS-08298.
        NTRS 19960020461.
    NASA SP-4225 — Shuttle-Mir History — STS-71: First Docking.
        https://www.nasa.gov/history/SP-4225/sts71/sts-71.htm
"""
from .soyuz_ms17 import Burn, MissionRef


STS71_MIR = MissionRef(
    mission_id="STS71_MIR",
    launch_utc="1995-06-27T19:32:19Z",
    dock_utc="1995-06-29T13:00:00Z",
    launch_to_dock_min=41.46 * 60,
    profile_orbits=27,
    burns=(
        Burn("PHASING", 0.0, 0.0, "Standard Shuttle phasing burns over ~41 h"),
        Burn("NCC", 0.0, 0.0, "NCC corrective burn"),
        Burn("TI", 0.0, 0.0, "Terminal Initiation"),
        Burn("BRAKE", 0.0, 0.0, "R-bar braking sequence to 76 m, then 9 m, then contact at 0.033 m/s"),
    ),
    total_dv_ms=0.0,
    target_port="Mir Kristall module (APAS-89)",
    gnc_system="Trajectory Control Sensor (TCS) + GPS + Orbiter Docking System (ODS)",
    capture_mechanism="APAS-89 (mounted on ODS in Atlantis payload bay)",
    granularity="HIGH",
    primary_doi="10.2514/1.19653",
    primary_url="https://ntrs.nasa.gov/citations/19960020461",
    notes=(
        "First Shuttle-Mir docking. Closing rate target 0.030 m/s; measured 0.033 m/s "
        "at contact. Alignment error <1 inch, <0.5 deg per NASA history. Crew exchange: "
        "Anatoly Solovyev/Nikolai Budarin to Mir; Norm Thagard returned (115-day mission)."
    ),
)
