"""Per-mission reference data parsers (read-only, hardcoded from open sources).

Currently includes:
    SOYUZ_MS17        — 2-orbit ultra-rapid (2020)
    APOLLO11_LM_RDV   — Lunar orbit rendezvous (1969)
    ATV1_JULES_VERNE  — First ATV automated docking (2008)
    HTV7_KOUNOTORI    — Berthing via Canadarm2 (2018)

Reference data hardcoded from primary sources with DOIs validated via Crossref.
See companion RPOD-50 dataset for the full archive.
"""
from .soyuz_ms17 import SOYUZ_MS17, Burn, MissionRef  # noqa: F401
from .apollo11 import APOLLO11_LM_RDV  # noqa: F401
from .atv1_jules_verne import ATV1_JULES_VERNE  # noqa: F401
from .htv7 import HTV7_KOUNOTORI  # noqa: F401

ALL_MISSIONS = [SOYUZ_MS17, APOLLO11_LM_RDV, ATV1_JULES_VERNE, HTV7_KOUNOTORI]
