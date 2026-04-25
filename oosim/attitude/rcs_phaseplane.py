"""RCS phase-plane (Schmitt trigger) bang-bang attitude control.

Operational spacecraft (Soyuz, Cygnus, ATV, HTV) use on-off RCS thrusters
controlled via phase-plane logic, not continuous PID. This module implements
the standard Schmitt trigger with hysteresis.

Reference: Wertz et al. (2011). SME-SMAD; Sidi (1997).
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class PhasePlaneParams:
    """Parameters for a phase-plane controller with hysteresis."""
    deadband_pos: float    # angular position deadband [rad]
    deadband_rate: float   # angular rate deadband [rad/s]
    hysteresis: float = 0.5  # fraction of deadband (0..1)


def phase_plane_command(angle_error: float, rate_error: float,
                        params: PhasePlaneParams,
                        previous_state: int = 0) -> int:
    """Schmitt-trigger output: -1 (negative thrust), 0 (off), +1 (positive thrust).

    Decision: switch line is angle_error + slope * rate_error = 0.
    Hysteresis is applied to avoid chattering.
    """
    switch = angle_error + (params.deadband_pos / max(params.deadband_rate, 1e-9)) * rate_error
    db = params.deadband_pos * params.hysteresis
    if previous_state == 0:
        if switch > params.deadband_pos:
            return -1
        if switch < -params.deadband_pos:
            return +1
        return 0
    if previous_state > 0 and switch > -db:
        return 0
    if previous_state < 0 and switch < db:
        return 0
    return previous_state
