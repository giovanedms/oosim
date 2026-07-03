"""Documented capture envelope presets from open-literature operational specifications.

Each preset corresponds to a documented operational mode and cites the primary
reference. These are the values used in Section 5 (Results) of the IAC paper.

Approval status (per discussion with co-author I. M. da Fonseca, ITA):
The team agreed on adopting these literature-documented values as the baseline
capture envelope until laboratory-specific values for the KUKA KR 1000 TITAN
at the SIVOR/ITA facility become available (planned for the A1 journal extension).

References:
    Lewis, J. L. & Donahoe, S. R. (2023). Space Vehicle Docking System
        Standardization. J. Space Safety Eng. 10(2), 127-132.
        DOI: 10.1016/j.jsse.2022.09.004 (preprint: NASA NTRS 20220004016).
    Ueda, S., Kasai, T., Uematsu, H. (2010). HTV Rendezvous Technique and GN&C
        Design Evaluation. AIAA. DOI: 10.2514/6.2010-7664.
    Miotto, P., Hannan, M. R., Beck, C. E. (2010). Designing and Validating
        Proximity Operations Rendezvous and Approach Trajectories for the Cygnus
        Mission. AIAA GNC. DOI: 10.2514/6.2010-8446.
"""
import numpy as np

from .capture_envelope import CaptureEnvelope


# -----------------------------------------------------------------------------
# Cygnus / HTV / Cargo Dragon-1 berthing capture box (Canadarm2 LEE grapple)
# -----------------------------------------------------------------------------
# The chaser free-drifts at the AI-30 (Approach Initiation 30 m) hold point,
# 10 m below ISS Harmony nadir CBM, in a small box from which Canadarm2's
# Latching End Effector (LEE) can extend and grasp the chaser's Flight
# Releasable Grapple Fixture (FRGF). Public values documented in Ueda 2010
# (HTV PROX system) and Miotto 2010 (Cygnus rendezvous design):
#
#   - Position box: ~+/-1 m lateral, ~+/-0.5 m radial (we use slightly tighter
#     ellipsoid as the inner-conservative inscribed approximation)
#   - Attitude alignment: ~+/-5 deg (Canadarm2 LEE has ~10 deg total grasp cone)
#   - Translational rate: <= 5 cm/s relative to capture box center
#   - Angular rate: <= 0.1 deg/s
CANADARM2_BERTHING = CaptureEnvelope(
    center_pos=np.array([10.0, 0.0, 0.0]),  # +10 m on R-bar (below ISS)
    pos_semi_axes=np.array([0.5, 0.5, 0.3]),  # m, inscribed inner ellipsoid
    target_quat=np.array([0.0, 0.0, 0.0, 1.0]),  # identity = aligned with LVLH
    att_tolerance_rad=np.deg2rad(5.0),
    vel_max=0.05,      # 5 cm/s
    omega_max=0.0017,  # 0.1 deg/s
)


# -----------------------------------------------------------------------------
# NDS / IDSS soft-capture spec (Crew Dragon, Cargo Dragon-2, Starliner)
# -----------------------------------------------------------------------------
# The NASA Docking System Block 1 (NDS) / International Docking System Standard
# (IDSS) soft-capture envelope is documented by Lewis & Donahoe (2023). The
# active vehicle must arrive at the docking interface within tighter bounds
# than berthing because the capture latches close immediately on contact.
NDS_DOCKING = CaptureEnvelope(
    center_pos=np.array([0.0, 0.0, 0.0]),
    pos_semi_axes=np.array([0.10, 0.10, 0.10]),  # 10 cm at the docking ring
    target_quat=np.array([0.0, 0.0, 0.0, 1.0]),
    att_tolerance_rad=np.deg2rad(2.0),
    vel_max=0.10,      # 10 cm/s axial closing rate is nominal
    omega_max=0.0035,  # 0.2 deg/s
)


# -----------------------------------------------------------------------------
# Soyuz / Progress SSVP-G4000 hard docking
# -----------------------------------------------------------------------------
# The Russian probe-and-drogue SSVP-G4000 system tolerates higher contact rates
# than soft-capture systems, but tighter angular alignment.
SSVP_DOCKING = CaptureEnvelope(
    center_pos=np.array([0.0, 0.0, 0.0]),
    pos_semi_axes=np.array([0.15, 0.15, 0.15]),
    target_quat=np.array([0.0, 0.0, 0.0, 1.0]),
    att_tolerance_rad=np.deg2rad(3.0),
    vel_max=0.10,
    omega_max=0.0070,  # 0.4 deg/s
)


__all__ = ["CANADARM2_BERTHING", "NDS_DOCKING", "SSVP_DOCKING"]
