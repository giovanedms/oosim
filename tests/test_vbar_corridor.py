"""Deterministic tests for the V-bar approach corridor.

LVLH convention: x = R-bar (radial), y = V-bar (along-track, approach axis;
chaser approaches from behind with y < 0), z = H-bar (cross-track).
Corridor: |x| <= slope_y*|y| + intercept_y, |z| <= slope_z*|y| + intercept_z
(defaults 0.10/5.0 and 0.05/3.0) — must stay consistent with the constraint
enforced by qp_terminal_target(enforce_vbar_corridor=True).
"""
import numpy as np
import pytest

from oosim.proxops.vbar import is_inside_corridor, vbar_corridor_bounds
from oosim.proxops.hcw import mean_motion
from oosim.targeting.qp_targeting import qp_terminal_target, HAVE_CVXPY


EARTH_RADIUS_KM = 6378.137
ISS_ALT_KM = 408.0


def test_point_on_approach_axis_inside():
    """Chaser 30 m behind the target on the approach axis is inside."""
    state = np.array([0.0, -30.0, 0.0, 0.0, 0.0, 0.0])
    assert is_inside_corridor(state)


def test_large_radial_deviation_outside():
    """|x| = 20 m at |y| = 30 m exceeds the radial bound 0.10*30 + 5 = 8 m."""
    state = np.array([20.0, -30.0, 0.0, 0.0, 0.0, 0.0])
    assert not is_inside_corridor(state)


def test_cross_track_symmetry():
    """z bound at |y| = 30 m is 0.05*30 + 3 = 4.5 m, symmetric in sign."""
    for z in (4.0, -4.0):
        assert is_inside_corridor(np.array([0.0, -30.0, z, 0.0, 0.0, 0.0]))
    for z in (5.0, -5.0):
        assert not is_inside_corridor(np.array([0.0, -30.0, z, 0.0, 0.0, 0.0]))


def test_bounds_are_affine_in_along_track_distance():
    """vbar_corridor_bounds returns (x_bound, z_bound) affine in |y|."""
    xb, zb = vbar_corridor_bounds(-30.0)
    assert xb == pytest.approx(0.10 * 30.0 + 5.0)
    assert zb == pytest.approx(0.05 * 30.0 + 3.0)


def test_agrees_with_qp_affine_constraint_form():
    """is_inside_corridor matches the QP constraint |x| <= -sy*y + by,
    |z| <= -sz*y + bz for y <= 0 points (same defaults)."""
    sy, by, sz, bz = 0.10, 5.0, 0.05, 3.0
    points = [
        (0.0, -30.0, 0.0), (20.0, -30.0, 0.0), (7.9, -30.0, 0.0),
        (8.1, -30.0, 0.0), (0.0, -30.0, 4.4), (0.0, -30.0, 4.6),
        (4.9, -0.0, 0.0), (5.1, -0.0, 0.0), (-7.0, -50.0, -3.0),
    ]
    for px, py, pz in points:
        state = np.array([px, py, pz, 0.0, 0.0, 0.0])
        qp_form = (abs(px) <= -sy * py + by) and (abs(pz) <= -sz * py + bz)
        assert is_inside_corridor(state) == qp_form, (px, py, pz)


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy not installed")
def test_consistency_with_qp_solver_feasibility():
    """A point inside the corridor is a feasible QP start under
    enforce_vbar_corridor; a point outside makes the QP infeasible."""
    n = mean_motion(EARTH_RADIUS_KM + ISS_ALT_KM)
    common = dict(
        target_pos=np.zeros(3), n=n, horizon_steps=1, dt=15.0,
        dv_max_per_step=10.0, terminal_mode="soft",
        enforce_vbar_corridor=True,
    )
    inside_pt = np.array([0.0, -30.0, 0.0, 0.0, 0.0, 0.0])
    outside_pt = np.array([20.0, -30.0, 0.0, 0.0, 0.0, 0.0])
    assert is_inside_corridor(inside_pt)
    assert qp_terminal_target(initial_state=inside_pt, **common).success
    assert not is_inside_corridor(outside_pt)
    assert not qp_terminal_target(initial_state=outside_pt, **common).success
