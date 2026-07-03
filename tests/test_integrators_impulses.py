"""Tests for integrate_with_impulses: impulse at t0, duplicate timestamps at
segment joins, and regression against manual segmented propagation."""
import numpy as np
import pytest

from oosim.utils.integrators import integrate_with_impulses


def _free_particle_rhs(t, y):
    """Trivial dynamics: dr/dt = v, dv/dt = 0 (exact segmented solution)."""
    dydt = np.zeros(6)
    dydt[:3] = y[3:]
    return dydt


def test_impulse_at_t0_is_applied():
    """An impulse scheduled exactly at t_span[0] changes the effective
    initial velocity (and hence the whole trajectory)."""
    t, y = integrate_with_impulses(
        _free_particle_rhs, np.zeros(6), (0.0, 10.0),
        impulses=[(0.0, np.array([1.0, 0.0, 0.0]))],
    )
    assert y[3, 0] == pytest.approx(1.0)   # first output sample post-impulse
    assert y[0, -1] == pytest.approx(10.0)  # x(10) = 1 m/s * 10 s


def test_no_duplicate_timestamps_at_breakpoints():
    """Output time grid is strictly increasing across impulse breakpoints."""
    impulses = [(3.0, np.array([0.0, 1.0, 0.0])),
                (7.0, np.array([0.0, 0.0, 1.0]))]
    state0 = np.array([0.0, 0.0, 0.0, 0.1, 0.0, 0.0])
    t, y = integrate_with_impulses(_free_particle_rhs, state0, (0.0, 10.0),
                                   impulses=impulses)
    assert len(np.unique(t)) == len(t)
    assert np.all(np.diff(t) > 0.0)


def test_breakpoint_sample_keeps_post_impulse_state():
    """The single sample emitted at an impulse time carries the post-impulse
    velocity (the pre-impulse duplicate is dropped)."""
    t, y = integrate_with_impulses(
        _free_particle_rhs, np.zeros(6), (0.0, 10.0),
        impulses=[(3.0, np.array([0.0, 1.0, 0.0]))],
    )
    idx = int(np.argmin(np.abs(t - 3.0)))
    assert t[idx] == pytest.approx(3.0)
    assert y[4, idx] == pytest.approx(1.0)


def test_two_mid_impulses_match_manual_segmented_propagation():
    """Regression: two mid-span impulses reproduce the exact piecewise
    free-particle solution at the final time."""
    state0 = np.array([0.0, 0.0, 0.0, 0.5, 0.0, 0.0])
    dv1, t1 = np.array([0.0, 1.0, 0.0]), 2.0
    dv2, t2 = np.array([-0.25, 0.0, 0.5]), 6.0
    t, y = integrate_with_impulses(_free_particle_rhs, state0, (0.0, 10.0),
                                   impulses=[(t1, dv1), (t2, dv2)])
    # Manual segmented propagation (free particle is exact):
    r, v = state0[:3].copy(), state0[3:].copy()
    r = r + v * t1
    v = v + dv1
    r = r + v * (t2 - t1)
    v = v + dv2
    r = r + v * (10.0 - t2)
    expected = np.concatenate([r, v])  # [4, 8, 2, 0.25, 1.0, 0.5]
    assert np.allclose(y[:, -1], expected, atol=1e-8)
    assert t[-1] == pytest.approx(10.0)
