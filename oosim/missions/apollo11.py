"""Apollo 11 CSM-LM lunar rendezvous reference data (July 1969).

The lunar orbit rendezvous (LOR) of Apollo 11 was performed by the Lunar Module
ascent stage (Eagle) catching up with the orbiting Command/Service Module
(Columbia) using a coelliptic profile (CSI/CDH/TPI/braking) developed by
Buzz Aldrin in his MIT doctoral thesis.

Reference (validated DOI):
    Hoag, D. (1983). The history of Apollo onboard guidance, navigation, and
        control. JGCD 6(1):4-13. DOI: 10.2514/3.19795
    NASA SP-238 — Apollo 11 Mission Report (1971). NTRS 19710015566.

Note: this is a lunar-orbit case (mu_moon, low altitude orbit), not Earth.
For consistency with the rest of OOSim (Earth-centric), only timeline + total
delta-v are used in the LEO-validation suite; for full Apollo lunar simulation
use the moon-centric variant in experiments/lunar/.
"""
from .soyuz_ms17 import Burn, MissionRef


APOLLO11_LM_RDV = MissionRef(
    mission_id="APOLLO11_LM_RDV",
    launch_utc="1969-07-21T17:54:00Z",       # LM ascent insertion
    dock_utc="1969-07-21T21:35:00Z",          # CSM dock
    launch_to_dock_min=221.0,                 # ~3 h 41 min from ascent
    profile_orbits=2,                         # ~2 LM orbits (CSI/CDH/TPI/braking)
    burns=(
        Burn("INSERT", 0.0, 1687.0, "Ascent insertion (LM ascent stage)"),
        Burn("CSI", 50.0, 15.5, "Coelliptic Sequence Initiation"),
        Burn("CDH", 80.0, 0.7, "Constant Delta H correction"),
        Burn("TPI", 130.0, 7.0, "Terminal Phase Initiation"),
        Burn("BRAKE", 200.0, 60.0, "Braking gates 6000/3000/1500/450/30 m"),
    ),
    total_dv_ms=1770.0,                       # includes ascent insertion
    target_port="CSM Columbia probe",
    gnc_system="PGNCS LM (AGC Block II) + Rendezvous Radar Ryan + AOT",
    capture_mechanism="Probe-and-drogue (CSM probe active) + 12 latches",
    granularity="HIGH",
    primary_doi="10.2514/3.19795",
    primary_url="https://ntrs.nasa.gov/citations/19710015566",
    notes=(
        "Lunar-orbit rendezvous (mu = mu_moon, not Earth). Δv excluding "
        "ascent-insertion burn = ~83 m/s, comparable in magnitude to LEO "
        "rendezvous profiles."
    ),
)
