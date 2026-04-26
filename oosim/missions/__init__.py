"""Per-mission reference data parsers (read-only, hardcoded from open sources).

Currently includes 14 missions:
    SOYUZ_MS17         — 2-orbit ultra-rapid Russian crewed (2020)
    APOLLO11_LM_RDV    — Lunar orbit rendezvous, NASA (1969)
    ATV1_JULES_VERNE   — First ATV automated docking, ESA (2008)
    HTV7_KOUNOTORI     — Berthing via Canadarm2, JAXA (2018)
    CYGNUS_NG21        — Berthing on Falcon 9, Northrop Grumman (2024)
    MEV1_INTELSAT901   — First commercial GEO servicing, Northrop SpaceLogistics (2020)
    ETSVII             — First autonomous robotic RVD, NASDA/JAXA (1997-99)
    CREW_DRAGON_DM2    — First crewed commercial flight, SpaceX (2020)
    CARGO_DRAGON_CRS21 — First US autonomous cargo docking, SpaceX (2020)
    ASTP               — First international docking (Apollo-Soyuz), 1975
    STS71_MIR          — First Shuttle-Mir docking, NASA (1995)
    SHENZHOU9          — First Chinese crewed docking + manual, CMSA (2012)
    TIANZHOU1          — First Chinese cargo automated docking, CMSA (2017)
    ELSAD              — First commercial magnetic capture, Astroscale (2021)

Reference data hardcoded from primary sources with DOIs validated via Crossref.
See companion RPOD-50 dataset for the full archive of 50 missions.
"""
from .soyuz_ms17 import SOYUZ_MS17, Burn, MissionRef  # noqa: F401
from .apollo11 import APOLLO11_LM_RDV  # noqa: F401
from .atv1_jules_verne import ATV1_JULES_VERNE  # noqa: F401
from .htv7 import HTV7_KOUNOTORI  # noqa: F401
from .cygnus_ng21 import CYGNUS_NG21  # noqa: F401
from .mev1 import MEV1_INTELSAT901  # noqa: F401
from .etsvii import ETSVII  # noqa: F401
from .crew_dragon_dm2 import CREW_DRAGON_DM2  # noqa: F401
from .cargo_dragon_crs21 import CARGO_DRAGON_CRS21  # noqa: F401
from .astp import ASTP  # noqa: F401
from .sts71_mir import STS71_MIR  # noqa: F401
from .shenzhou9 import SHENZHOU9  # noqa: F401
from .tianzhou1 import TIANZHOU1  # noqa: F401
from .elsad import ELSAD  # noqa: F401

ALL_MISSIONS = [
    SOYUZ_MS17, APOLLO11_LM_RDV, ATV1_JULES_VERNE, HTV7_KOUNOTORI,
    CYGNUS_NG21, MEV1_INTELSAT901, ETSVII,
    CREW_DRAGON_DM2, CARGO_DRAGON_CRS21, ASTP, STS71_MIR,
    SHENZHOU9, TIANZHOU1, ELSAD,
]
