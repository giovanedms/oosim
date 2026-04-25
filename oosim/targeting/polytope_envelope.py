"""SOC-compatible workspace polytope for capture envelope (extension to 3.2).

The axis-aligned ellipsoid (`CaptureEnvelope` + `envelope_specs`) is a
conservative inner approximation of the true manipulator workspace. For
manipulators with markedly non-convex reachable volumes (multi-arm cases,
end-effectors with constrained roll), a polytope built from a small number of
half-spaces can capture more of the true workspace while remaining QP-tractable
(linear inequalities are trivially convex and second-order-cone-compatible).

This module provides the data structures and helpers; the QP integration is
exposed via `qp_terminal_target_polytope` (forthcoming, A1 journal extension).
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class WorkspacePolytope:
    """Workspace described as { r in R^3 : A r <= b }.

    Args:
        A: m x 3 matrix of half-space normals.
        b: m-vector of half-space offsets.

    The polytope is the intersection of m half-spaces. The set is convex
    (intersection of convex sets) and bounded if the half-spaces enclose a
    finite region.
    """
    A: np.ndarray
    b: np.ndarray
    label: str = "polytope"

    def __post_init__(self):
        self.A = np.asarray(self.A, dtype=float)
        self.b = np.asarray(self.b, dtype=float)
        assert self.A.ndim == 2 and self.A.shape[1] == 3
        assert self.b.ndim == 1 and self.b.shape[0] == self.A.shape[0]

    def contains(self, r: np.ndarray) -> bool:
        """Test whether a point lies inside the polytope."""
        return bool(np.all(self.A @ r <= self.b + 1e-9))

    @classmethod
    def axis_aligned_box(cls, center: np.ndarray, half_extents: np.ndarray,
                         label: str = "box") -> "WorkspacePolytope":
        """Construct a box centered at `center` with given half-extents."""
        A = np.vstack([np.eye(3), -np.eye(3)])
        b = np.concatenate([center + half_extents, -(center - half_extents)])
        return cls(A=A, b=b, label=label)


# Documented preset: the Canadarm2 capture box modeled as a polytope.
# This is an approximate description — true workspace has small concavities
# near the wrist-roll singularity that cannot be exactly captured by a finite
# polytope, but the box approximation is consistent with the published
# operational limits of the LEE grapple.
CANADARM2_POLYTOPE = WorkspacePolytope.axis_aligned_box(
    center=np.array([10.0, 0.0, 0.0]),
    half_extents=np.array([0.5, 0.5, 0.3]),
    label="canadarm2_box",
)
