"""V-bar approach corridor enforcement.

The V-bar (velocity-vector) corridor constrains the chaser's lateral and vertical
deviations to a cone narrowing toward the target. Standard reference:

    NASA SSP 50808, ISS to Commercial Orbital Transportation Services Interface
    Requirements Document, NASA Johnson Space Center.
    Fehse, W. (2003). Automated Rendezvous and Docking of Spacecraft. Cambridge UP.
"""
import numpy as np


def vbar_corridor_bounds(y: float, slope_y: float = 0.10, intercept_y: float = 5.0,
                         slope_z: float = 0.05, intercept_z: float = 3.0) -> tuple[float, float]:
    """Compute |x| (radial) and |z| (cross-track) bounds at along-track distance y.

    LVLH convention: x = R-bar (radial), y = V-bar (along-track, approach axis;
    chaser approaches from behind with y < 0), z = H-bar (cross-track).
    Consistent with the corridor constraint in targeting.qp_targeting
    (parameter names slope_y/slope_z match vbar_slope_y/vbar_slope_z there).

    Default values from publicly documented Soyuz/Progress approach corridors.

    Args:
        y: along-track distance to target [m] (negative behind target on V-bar).
        slope_y, intercept_y: cone parameters for radial (x) bound:
            |x| <= slope_y*|y| + intercept_y.
        slope_z, intercept_z: cone parameters for cross-track (z) bound:
            |z| <= slope_z*|y| + intercept_z.

    Returns:
        (x_bound, z_bound) in meters.
    """
    return slope_y * abs(y) + intercept_y, slope_z * abs(y) + intercept_z


def is_inside_corridor(state: np.ndarray, **kwargs) -> bool:
    """Check whether LVLH state [x, y, z, ...] is inside the V-bar corridor.

    The approach distance is |y| = |state[1]| (along-track); radial (x) and
    cross-track (z) deviations are bounded by affine cones in |y|.
    """
    x, y, z = state[0], state[1], state[2]
    xb, zb = vbar_corridor_bounds(y, **kwargs)
    return abs(x) <= xb and abs(z) <= zb
