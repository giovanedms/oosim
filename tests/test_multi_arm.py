"""Tests for multi-arm reachability."""
import numpy as np
from oosim.targeting.multi_arm import (
    MultiArmEnvelope, contains_union, contains_intersection,
    inscribed_intersection_ellipsoid,
    ISS_THREE_ARM_INTERSECTION, ISS_THREE_ARM_UNION,
)


def test_union_accepts_any_workspace_member():
    """A point inside JEMRMS (offset to +y) should pass the union test."""
    pos = np.array([10.0, 5.0, 0.0])  # JEMRMS center
    assert contains_union(ISS_THREE_ARM_UNION, pos)


def test_intersection_rejects_jemrms_only_point():
    """A point at the JEMRMS center is OUTSIDE the Canadarm2 envelope."""
    pos = np.array([10.0, 5.0, 0.0])
    assert not contains_intersection(ISS_THREE_ARM_INTERSECTION, pos)


def test_intersection_handles_disjoint_workspaces():
    """When the three arm workspaces are too far apart to have a non-trivial
    intersection, the inscribed-ellipsoid helper should collapse to a tiny
    point — signalling 'no overlap' to the caller."""
    inscribed = inscribed_intersection_ellipsoid(ISS_THREE_ARM_INTERSECTION)
    # Either the inscribed ellipsoid is tiny (collapsed) or its center is inside
    # all three arms by construction.
    if all(s > 0.01 for s in inscribed.pos_semi_axes):
        # Real intersection found — center should be inside all
        assert contains_intersection(ISS_THREE_ARM_INTERSECTION, inscribed.center_pos)
    else:
        # Collapsed — no genuine intersection
        assert all(s <= 0.05 for s in inscribed.pos_semi_axes)


def test_inscribed_ellipsoid_smaller_than_individual():
    """The inscribed intersection ellipsoid must have smaller semi-axes than
    any individual arm's semi-axes (it's a conservative inner approximation)."""
    inscribed = inscribed_intersection_ellipsoid(ISS_THREE_ARM_INTERSECTION)
    for arm in ISS_THREE_ARM_INTERSECTION.arms:
        assert all(inscribed.pos_semi_axes <= arm.pos_semi_axes)
