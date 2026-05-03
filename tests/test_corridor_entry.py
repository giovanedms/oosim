"""Tests for M9 approach-corridor entry maneuver."""
import numpy as np
import pytest

from oosim.scenarios.corridor_entry import (
    CorridorEntryPlan, enter_approach_corridor,
)
from oosim.proxops.coupled_state import MU_EARTH
from oosim.utils.frames_dynamic import lvlh_relative_to_eci_state

R_E = 6378.137
SOYUZ_THRUST = 5.6e-5


def make_iss_circular(alt=420.0):
    a = R_E + alt
    v = np.sqrt(MU_EARTH / a)
    return np.concatenate([[a, 0., 0.], [0., v, 0.]])


def chaser_at_lvlh_offset(target, dr_lvlh_m, dv_lvlh_m_s=None):
    if dv_lvlh_m_s is None:
        dv_lvlh_m_s = np.zeros(3)
    rel = np.concatenate([np.asarray(dr_lvlh_m) / 1000.0,
                          np.asarray(dv_lvlh_m_s) / 1000.0])
    r, v = lvlh_relative_to_eci_state(rel, target[:3], target[3:6], mu=MU_EARTH)
    return np.concatenate([r, v])


def test_collocated_chaser_to_50m_v_bar():
    """Chaser at target → hold point [0,-50,0] m: arrives within 1 m, near-zero v."""
    target = make_iss_circular()
    chaser = chaser_at_lvlh_offset(target, [0., 0., 0.])
    plan = enter_approach_corridor(
        chaser, target, hold_point_lvlh_m=np.array([0., -50., 0.]),
        transfer_time_s=600.0, thrust_acceleration=SOYUZ_THRUST,
    )
    assert isinstance(plan, CorridorEntryPlan)
    achieved = plan.final_relative_state_lvlh[:3] * 1000.0   # m
    assert np.linalg.norm(achieved - np.array([0., -50., 0.])) < 1.0
    achieved_v = plan.final_relative_state_lvlh[3:6] * 1000.0   # m/s
    assert np.linalg.norm(achieved_v) < 0.01    # < 1 cm/s


def test_two_burns_and_positive_total_dv():
    target = make_iss_circular()
    chaser = chaser_at_lvlh_offset(target, [0., 0., 0.])
    plan = enter_approach_corridor(
        chaser, target, hold_point_lvlh_m=np.array([0., -50., 0.]),
        transfer_time_s=600.0,
    )
    assert len(plan.burns) == 2
    assert plan.total_dv_m_s > 0.0
    # Both burns have positive durations (finite-burn correction applied)
    assert plan.burns[0].duration > 0.0
    assert plan.burns[1].duration > 0.0


def test_singular_transfer_time_raises():
    """transfer_time = π/n is a singular point of HCW STM."""
    target = make_iss_circular()
    chaser = chaser_at_lvlh_offset(target, [0., 0., 0.])
    a = float(np.linalg.norm(target[:3]))
    n = float(np.sqrt(MU_EARTH / a**3))
    t_singular = np.pi / n
    with pytest.raises(ValueError, match="singular"):
        enter_approach_corridor(
            chaser, target, hold_point_lvlh_m=np.array([0., -50., 0.]),
            transfer_time_s=t_singular,
        )


def test_offset_chaser_reaches_corridor_too():
    """Chaser starting 200 m off-corridor still arrives within 1 m of hold point."""
    target = make_iss_circular()
    chaser = chaser_at_lvlh_offset(target, [10., 200., -5.])  # off in all 3 axes
    plan = enter_approach_corridor(
        chaser, target, hold_point_lvlh_m=np.array([0., -50., 0.]),
        transfer_time_s=900.0,
    )
    achieved = plan.final_relative_state_lvlh[:3] * 1000.0
    assert np.linalg.norm(achieved - np.array([0., -50., 0.])) < 1.0


def test_dv_scales_with_distance():
    """Larger displacements should require larger Δv (sanity)."""
    target = make_iss_circular()
    chaser = chaser_at_lvlh_offset(target, [0., 0., 0.])
    plan_50 = enter_approach_corridor(
        chaser, target, np.array([0., -50., 0.]), transfer_time_s=600.0,
    )
    plan_500 = enter_approach_corridor(
        chaser, target, np.array([0., -500., 0.]), transfer_time_s=600.0,
    )
    assert plan_500.total_dv_m_s > plan_50.total_dv_m_s
