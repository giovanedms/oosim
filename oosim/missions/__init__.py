"""Per-mission reference data parsers (read-only, hardcoded from open sources).

Currently includes:
    SOYUZ_MS17         — 2-orbit ultra-rapid Russian crewed (2020)
    APOLLO11_LM_RDV    — Lunar orbit rendezvous, NASA (1969)
    ATV1_JULES_VERNE   — First ATV automated docking, ESA (2008)
    HTV7_KOUNOTORI     — Berthing via Canadarm2, JAXA (2018)
    CYGNUS_NG21        — Berthing on Falcon 9, Northrop Grumman (2024)
    MEV1_INTELSAT901   — First commercial GEO servicing, Northrop SpaceLogistics (2020)
    ETSVII             — First autonomous robotic RVD, NASDA/JAXA (1997-99)

Reference data hardcoded from primary sources with DOIs validated via Crossref.
See companion RPOD-50 dataset for the full archive.
"""
from .soyuz_ms17 import SOYUZ_MS17, Burn, MissionRef  # noqa: F401
from .apollo11 import APOLLO11_LM_RDV  # noqa: F401
from .atv1_jules_verne import ATV1_JULES_VERNE  # noqa: F401
from .htv7 import HTV7_KOUNOTORI  # noqa: F401
from .cygnus_ng21 import CYGNUS_NG21  # noqa: F401
from .mev1 import MEV1_INTELSAT901  # noqa: F401
from .etsvii import ETSVII  # noqa: F401

ALL_MISSIONS = [
    SOYUZ_MS17, APOLLO11_LM_RDV, ATV1_JULES_VERNE, HTV7_KOUNOTORI,
    CYGNUS_NG21, MEV1_INTELSAT901, ETSVII,
]
