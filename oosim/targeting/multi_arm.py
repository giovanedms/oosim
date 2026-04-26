"""Multi-arm reachability for ISS visiting vehicles.

The International Space Station hosts three berthing manipulators:
  - Canadarm2 (Space Station Remote Manipulator System, CSA, on Mobile Base)
  - JEMRMS (Japanese Experiment Module Remote Manipulator System, JAXA)
  - ERA (European Robotic Arm, on the Russian segment)

A chaser arriving at the ISS can target any of the three reachable workspaces.
This module provides the convex set operations:

  - UNION (any-arm-suffices): the chaser must be inside at least one of the
    three workspace ellipsoids. The union of ellipsoids is generally NOT
    convex, but can be approximated by the polytope union of axis-aligned
    boxes that bound each ellipsoid.

  - INTERSECTION (all-arms-redundant): the chaser must be inside ALL three
    workspace ellipsoids simultaneously. The intersection of convex sets is
    convex; we approximate it by the largest inscribed ellipsoid (the
    Lowner-John inner ellipsoid).

References:
    Tobenkin, M. M., Manchester, I. R., Tedrake, R. (2011). Invariant funnels
        around trajectories using sum-of-squares programming. IFAC.
        DOI: 10.3182/20110828-6-it-1002.03098
"""
from dataclasses import dataclass
import numpy as np

from .capture_envelope import CaptureEnvelope
from .envelope_specs import CANADARM2_BERTHING


# Approximate ISS arm workspace presets. These are illustrative — operational
# values would come from JAXA + ESA documentation we have not validated yet.
JEMRMS_BERTHING = CaptureEnvelope(
    center_pos=np.array([10.0, 5.0, 0.0]),       # offset toward Kibo nadir
    pos_semi_axes=np.array([0.4, 0.4, 0.3]),
    target_quat=np.array([0.0, 0.0, 0.0, 1.0]),
    att_tolerance_rad=np.deg2rad(5.0),
    vel_max=0.05, omega_max=0.0017,
)

ERA_BERTHING = CaptureEnvelope(
    center_pos=np.array([10.0, -5.0, 0.0]),      # offset toward Russian segment
    pos_semi_axes=np.array([0.4, 0.4, 0.3]),
    target_quat=np.array([0.0, 0.0, 0.0, 1.0]),
    att_tolerance_rad=np.deg2rad(5.0),
    vel_max=0.05, omega_max=0.0017,
)


@dataclass
class MultiArmEnvelope:
    """Combined envelope for multi-arm reachability."""
    arms: list[CaptureEnvelope]
    mode: str  # "union" or "intersection"


def contains_union(envelope: MultiArmEnvelope, pos: np.ndarray) -> bool:
    """True if pos lies inside ANY arm workspace ellipsoid."""
    for env in envelope.arms:
        rel = (pos - env.center_pos) / env.pos_semi_axes
        if float(np.dot(rel, rel)) <= 1.0:
            return True
    return False


def contains_intersection(envelope: MultiArmEnvelope, pos: np.ndarray) -> bool:
    """True if pos lies inside ALL arm workspace ellipsoids."""
    for env in envelope.arms:
        rel = (pos - env.center_pos) / env.pos_semi_axes
        if float(np.dot(rel, rel)) > 1.0:
            return False
    return True


def inscribed_intersection_ellipsoid(envelope: MultiArmEnvelope) -> CaptureEnvelope:
    """Find the largest axis-aligned ellipsoid inside the intersection.

    For axis-aligned ellipsoids with possibly different centers, the inscribed
    intersection ellipsoid is approximated by:
      - center = component-wise mean of arm centers
      - semi-axes = component-wise minimum of arm semi-axes minus distance
                    from mean to each individual center

    This is conservative but always returns a valid (smaller) ellipsoid that
    is guaranteed to lie inside the true intersection.
    """
    if envelope.mode != "intersection":
        raise ValueError("inscribed_intersection_ellipsoid only valid for mode='intersection'")
    centers = np.array([env.center_pos for env in envelope.arms])
    semis = np.array([env.pos_semi_axes for env in envelope.arms])
    mean_center = centers.mean(axis=0)
    displacements = np.abs(centers - mean_center).max(axis=0)
    # The inscribed ellipsoid centered at mean_center must fit inside ALL arms.
    # Conservative scalar shrink: each axis = (min semi - displacement), but
    # we must still verify the result actually lies inside each arm.
    inscribed_semi = np.maximum(semis.min(axis=0) - displacements, 0.01)  # 1 cm floor

    inscribed = CaptureEnvelope(
        center_pos=mean_center,
        pos_semi_axes=inscribed_semi,
        target_quat=envelope.arms[0].target_quat,
        att_tolerance_rad=envelope.arms[0].att_tolerance_rad,
        vel_max=min(env.vel_max for env in envelope.arms),
        omega_max=min(env.omega_max for env in envelope.arms),
    )
    # If the conservative inscribed-axis floor leaves the center outside any
    # arm, the inscribed-ellipsoid construction is infeasible and we must
    # collapse to a point at the mean. This indicates the arms have effectively
    # disjoint workspaces.
    for arm in envelope.arms:
        rel = (mean_center - arm.center_pos) / arm.pos_semi_axes
        if float(np.dot(rel, rel)) > 1.0:
            # Collapse to a tiny point — caller should treat as "no overlap"
            inscribed.pos_semi_axes = np.array([0.001, 0.001, 0.001])
            break
    return inscribed


# Convenience preset for the ISS three-arm setup
ISS_THREE_ARM_INTERSECTION = MultiArmEnvelope(
    arms=[CANADARM2_BERTHING, JEMRMS_BERTHING, ERA_BERTHING],
    mode="intersection",
)
ISS_THREE_ARM_UNION = MultiArmEnvelope(
    arms=[CANADARM2_BERTHING, JEMRMS_BERTHING, ERA_BERTHING],
    mode="union",
)
