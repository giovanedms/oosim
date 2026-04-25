"""Tests for workspace polytope envelope."""
import numpy as np
from oosim.targeting.polytope_envelope import WorkspacePolytope, CANADARM2_POLYTOPE


def test_box_contains_center():
    box = WorkspacePolytope.axis_aligned_box(np.zeros(3), np.array([1.0, 1.0, 1.0]))
    assert box.contains(np.zeros(3))


def test_box_excludes_outside_point():
    box = WorkspacePolytope.axis_aligned_box(np.zeros(3), np.array([1.0, 1.0, 1.0]))
    assert not box.contains(np.array([2.0, 0., 0.]))


def test_canadarm2_polytope_matches_envelope():
    """The polytope should contain a point well inside the documented box."""
    assert CANADARM2_POLYTOPE.contains(np.array([10.0, 0.0, 0.0]))
    assert CANADARM2_POLYTOPE.contains(np.array([10.2, 0.1, 0.05]))
    assert not CANADARM2_POLYTOPE.contains(np.array([15.0, 0., 0.]))
