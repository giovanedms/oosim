"""ATV-1 Jules Verne — first European Automated Transfer Vehicle (March-September 2008).

The first ATV demonstrated full automated rendezvous and docking with the
Russian Zvezda Service Module aft port, including two Demonstration Days
where the vehicle held at the S2 (3.5 km) and S41 (11 m) hold points for
in-flight checkout of the GNC system before final docking.

Reference (validated DOI):
    Baize, L. et al. (2008). The ATV "Jules Verne" Supplies the ISS.
        SpaceOps 2008 Conference. DOI: 10.2514/6.2008-3537
    Baize, L. & Novelli, A. (2010). ATV "Jules Verne" Control Center,
        from Challenges to Success. SpaceOps 2010. DOI: 10.2514/6.2010-2124
"""
from .soyuz_ms17 import Burn, MissionRef


ATV1_JULES_VERNE = MissionRef(
    mission_id="ATV1_JULES_VERNE",
    launch_utc="2008-03-09T03:03:00Z",
    dock_utc="2008-04-03T14:40:00Z",
    launch_to_dock_min=611.62 * 60,           # ~25.5 days (incl. Demo Days)
    profile_orbits=400,                        # very long phasing + checkout
    burns=(
        # Per-burn delta-v not published in open literature; aggregate values only.
        Burn("PHASING", 0.0, 0.0, "Multiple phasing burns over ~3 weeks (per-burn not public)"),
        Burn("DEMO_DAY1", 0.0, 0.0, "Hold at S2 (3.5 km) for GNC checkout"),
        Burn("DEMO_DAY2", 0.0, 0.0, "Hold at S41 (11 m) for final checkout"),
    ),
    total_dv_ms=0.0,                           # NOT PUBLISHED — see notes
    target_port="ISS Zvezda aft port (SSVP-G4000)",
    gnc_system="Kurs-P + RGPS + Videometer (LIDAR retro-reflectors) + Telegoniometer",
    capture_mechanism="SSVP-G4000 androgynous (ATV variant)",
    granularity="HIGH",                        # high in timeline + GNC system, low in dv
    primary_doi="10.2514/6.2008-3537",
    primary_url="https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/ATV/ATV-1_i_Jules_Verne_i",
    notes=(
        "Per-burn delta-v not in open literature. Aggregate propellant: 811 kg "
        "transferred to ISS. ATV launch mass 19,360 kg. Two Demo Days held "
        "at S2 (3.5 km) and S41 (11 m) before final docking. One real "
        "collision-avoidance burn during the mission for orbital debris."
    ),
)
