"""V-bar approach corridor enforcement.

The V-bar (velocity-vector) corridor constrains the chaser's lateral and vertical
deviations to a cone narrowing toward the target. Standard reference:

    NASA SSP 50808, ISS to Commercial Orbital Transportation Services Interface
    Requirements Document, NASA Johnson Space Center.
    Fehse, W. (2003). Automated Rendezvous and Docking of Spacecraft. Cambridge UP.
"""
import numpy as np


def vbar_corridor_bounds(x: float, slope_y: float = 0.10, intercept_y: float = 5.0,
                         slope_z: float = 0.05, intercept_z: float = 3.0) -> tuple[float, float]:
    """Compute |y| and |z| bounds at along-track distance x from target.

    Default values from publicly documented Soyuz/Progress approach corridors.

    Args:
        x: along-track distance to target [m] (positive behind target on V-bar).
        slope_y, intercept_y: cone parameters for lateral (y) bound: |y| < slope*x + intercept.
        slope_z, intercept_z: cone parameters for vertical (z) bound.

    Returns:
        (y_bound, z_bound) in meters.
    """
    return slope_y * abs(x) + intercept_y, slope_z * abs(x) + intercept_z


def is_inside_corridor(state: np.ndarray, **kwargs) -> bool:
    """Check whether HCW state [x, y, z, ...] is inside V-bar corridor."""
    x, y, z = state[0], state[1], state[2]
    yb, zb = vbar_corridor_bounds(x, **kwargs)
    return abs(y) <= yb and abs(z) <= zb
