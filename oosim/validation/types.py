"""Core dataclasses and enums for the F3-real validation framework.

Kept in a separate module with zero intra-project imports so that
oosim/scenarios/atv1.py can import MissionScenario and ValidationTier
without triggering the circular dependency chain:
  oosim.validation.__init__ → mission_runner → oosim.scenarios.* →
  oosim.scenarios.__init__ → atv1 → oosim.validation.mission_runner  (cycle)
"""
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class ValidationTier(Enum):
    TIER_A = "A"   # published Δv
    TIER_B = "B"   # reverse-engineered Δv
    TIER_C = "C"   # qualitative only


@dataclass
class MissionScenario:
    """Inputs for one mission's reproduction."""
    name: str
    year: int
    chaser_initial_eci: np.ndarray         # (6,) [km, km/s] post-insertion
    target_initial_eci: np.ndarray         # (6,) [km, km/s]
    expected_dv_total_m_s: float           # published or reverse-engineered
    expected_duration_min: float
    tier: ValidationTier
    inertia: np.ndarray                    # (3,3) [kg·m²]
    thrust_acceleration: float = 5.6e-5    # [km/s²]
    n_phase_orbits: int = 2
    t_terminal: float = 400.0              # [s]
    target_pos_lvlh_m: np.ndarray = field(default_factory=lambda: np.array([0., -10., 0.]))
    references: list = field(default_factory=list)  # primary source citations
    notes: str = ""


@dataclass
class MissionRunResult:
    """Pipeline output (from M5+M8+M6)."""
    phasing_dv_m_s: float        # M5 total impulsive
    drift_dv_m_s: float          # M8 sum
    terminal_dv_m_s: float       # M6 sum
    total_dv_m_s: float
    phasing_time_s: float
    drift_time_s: float
    total_duration_s: float
    terminal_distance_m: float
    n_terminal_impulses: int


@dataclass
class ValidationReport:
    """Comparison of MissionRunResult vs scenario expectations."""
    scenario: MissionScenario
    result: MissionRunResult
    dv_error_relative: float          # (sim - expected) / expected
    duration_error_relative: float
    tolerance_dv: float               # tier-defined threshold
    tolerance_duration: float
    passed_dv: bool
    passed_duration: bool
    passed_overall: bool
    summary: str
