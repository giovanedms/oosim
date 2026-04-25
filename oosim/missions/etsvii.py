"""ETS-VII Hikoboshi/Orihime — first autonomous robotic rendezvous (1997-99).

Engineering Test Satellite VII, launched by NASDA (now JAXA) on H-II Flight 6
in November 1997, performed the world's FIRST fully autonomous, unmanned
rendezvous and docking experiments with an integrated robotic manipulator.
The mission flew with two physical spacecraft separable in orbit — Hikoboshi
(chaser, 2,500 kg) and Orihime (target, 410 kg) — and performed three
distinct RVD experiments (RVD-1 in July 1998, RVD-2 in August 1998, RVD-3
in October 1998), plus extensive robotic manipulation experiments.

ETS-VII is foundational for every modern autonomous RVD program: HTV, ATV,
Crew Dragon NDS, MEV — all trace lineage to its sensor architecture
(RGPS + PXS + RVS) and its proof that fully autonomous capture is feasible.

References (validated DOIs):
    Kawano, I., Mokuno, M., Kasai, T., Suzuki, T. (2001). Result of Autonomous
        Rendezvous Docking Experiment of Engineering Test Satellite-VII.
        J. Spacecraft and Rockets 38(1):105-111. DOI: 10.2514/2.3661
    Ohkami, Y. & Kawano, I. (2003). Autonomous rendezvous and docking by ETS-VII:
        a challenge of Japan in GNC — Breakwell Memorial Lecture.
        Acta Astronautica 53(1):1-8. DOI: 10.1016/S0094-5765(02)00195-9
"""
from .soyuz_ms17 import Burn, MissionRef


ETSVII = MissionRef(
    mission_id="ETSVII",
    launch_utc="1997-11-28T00:00:00Z",         # NASDA H-II Flight 6
    dock_utc="1998-07-07T00:00:00Z",           # First successful RVD-1
    launch_to_dock_min=222.0 * 24 * 60,        # ~222 days from launch to first RVD
    profile_orbits=3300,                        # ~7 months of preparation
    burns=(
        Burn("INSERT", 0.0, 0.0, "Initial orbit insertion (550 km circular SSO-like)"),
        Burn("SEPARATE", 0.0, 0.0, "Separation of Orihime from Hikoboshi"),
        Burn("PHASING", 0.0, 0.0, "Phasing burns to establish stable relative orbit"),
        Burn("RVD1", 0.0, 0.0, "RVD-1 final approach + docking (Jul 1998)"),
    ),
    total_dv_ms=0.0,
    target_port="Orihime docking interface (proprietary NASDA/JAXA)",
    gnc_system="RGPS (Relative GPS) + PXS (Proximity Sensor) + RVS (laser Rendezvous Sensor) + 6-DOF arm 2 m",
    capture_mechanism="Active docking probe + post-docking robotic capture experiments",
    granularity="HIGH",
    primary_doi="10.2514/2.3661",
    primary_url="https://global.jaxa.jp/press/nasda/2002/ets7_20021031_e.html",
    notes=(
        "World's first autonomous unmanned RVD with integrated manipulator. "
        "Three experiments: RVD-1 (Jul 1998 success), RVD-2 (Aug 1998), "
        "RVD-3 (Oct 1998). Robotic experiments with the 2 m manipulator continued "
        "until December 1999. Foundational for HTV PROX, ATV GNC, and modern "
        "automated RVD architectures. Breakwell Memorial Lecture by Ohkami & "
        "Kawano (Acta Astronautica 2003) is the canonical reference."
    ),
)
