"""Tests for the 13-dim coupled state propagator (Module 3, F2-real)."""
import numpy as np
import pytest
from oosim.proxops.coupled_state import (
    CoupledStateConfig, coupled_dynamics, propagate_coupled,
    make_initial_state, quat_to_rotation_matrix, quat_omega_matrix,
    MU_EARTH,
)


# Standard small-spacecraft inertia (Soyuz-class, kg·m²)
INERTIA_SOYUZ = np.diag([3850.0, 3920.0, 1240.0])


def test_quat_to_rotation_identity():
    """Identity quaternion yields identity rotation."""
    q = np.array([0.0, 0.0, 0.0, 1.0])
    R = quat_to_rotation_matrix(q)
    assert np.allclose(R, np.eye(3), atol=1e-12)


def test_initial_state_default_identity_quaternion():
    r = np.array([7000.0, 0.0, 0.0])
    v = np.array([0.0, 7.546, 0.0])
    s = make_initial_state(r, v)
    assert s.shape == (13,)
    assert np.allclose(s[6:10], [0., 0., 0., 1.])
    assert np.allclose(s[10:13], 0.)


def test_propagate_circular_orbit_no_torque_no_thrust():
    """Pure Kepler orbit with no attitude actuation: position returns after T."""
    a = 7000.0  # km
    v_circ = np.sqrt(MU_EARTH / a)
    state0 = make_initial_state(
        r_eci=[a, 0., 0.], v_eci=[0., v_circ, 0.],
    )
    cfg = CoupledStateConfig(inertia=INERTIA_SOYUZ)
    period = 2 * np.pi * np.sqrt(a**3 / MU_EARTH)
    t_eval = np.array([0.0, period])
    t, x = propagate_coupled(state0, (0.0, period), cfg, t_eval=t_eval, rtol=1e-11)
    # Position should be very close to initial after one period
    assert np.linalg.norm(x[0:3, -1] - state0[0:3]) < 1.0  # 1 km tolerance
    # Velocity should also close
    assert np.linalg.norm(x[3:6, -1] - state0[3:6]) < 1e-3
    # Attitude unchanged
    assert np.linalg.norm(x[6:10, -1] - state0[6:10]) < 1e-9


def test_attitude_free_spin_preserves_unit_quaternion():
    """Free-spin (no torque, no thrust): quaternion stays unit-norm."""
    state0 = make_initial_state(
        r_eci=[7000., 0., 0.], v_eci=[0., 7.5, 0.],
        omega=[0.01, 0.02, -0.005],
    )
    cfg = CoupledStateConfig(inertia=INERTIA_SOYUZ)
    t, x = propagate_coupled(state0, (0.0, 600.0), cfg, t_eval=np.linspace(0, 600, 20))
    norms = np.linalg.norm(x[6:10, :], axis=0)
    assert np.allclose(norms, 1.0, atol=1e-9)


def test_constant_thrust_changes_velocity():
    """A constant body-frame thrust must change ECI velocity (gravity-baseline-subtracted).

    Over 60 s at r=7000 km, gravity contributes ≈ -0.49 km/s in vx (dominant).
    To isolate the thrust effect we subtract a baseline propagation with no thrust.
    """
    state0 = make_initial_state(
        r_eci=[7000., 0., 0.], v_eci=[0., 7.5, 0.],
    )
    # 0.001 km/s² along body-x (which == ECI-x with identity attitude)
    def thrust_cb(t, x):
        return np.array([0.001, 0., 0.])
    cfg_thrust = CoupledStateConfig(inertia=INERTIA_SOYUZ, thrust_callback=thrust_cb)
    cfg_baseline = CoupledStateConfig(inertia=INERTIA_SOYUZ)
    t1, x1 = propagate_coupled(state0, (0.0, 60.0), cfg_thrust, t_eval=np.array([0., 60.]), rtol=1e-11)
    t0, x0 = propagate_coupled(state0, (0.0, 60.0), cfg_baseline, t_eval=np.array([0., 60.]), rtol=1e-11)
    dv_thrust_only = x1[3:6, -1] - x0[3:6, -1]
    # 0.001 km/s² × 60 s = 0.06 km/s in ECI-x; expect > 50 m/s in x, ~zero in y/z
    assert dv_thrust_only[0] > 0.05
    assert abs(dv_thrust_only[1]) < 1e-3
    assert abs(dv_thrust_only[2]) < 1e-6


def test_constant_torque_changes_omega():
    """A constant body-frame torque must change angular velocity."""
    state0 = make_initial_state(
        r_eci=[7000., 0., 0.], v_eci=[0., 7.5, 0.],
    )
    def torque_cb(t, x):
        return np.array([10.0, 0., 0.])  # 10 N·m about body-x
    cfg = CoupledStateConfig(inertia=INERTIA_SOYUZ, torque_callback=torque_cb)
    t, x = propagate_coupled(state0, (0.0, 100.0), cfg, t_eval=np.array([0., 100.]))
    omega_x = x[10, -1]
    # I_xx = 3850; torque 10 over 100 s → Δω_x ≈ 10*100/3850 ≈ 0.26 rad/s
    expected = 10.0 * 100.0 / 3850.0
    assert abs(omega_x - expected) < 0.01


def test_quaternion_normalised_in_output():
    """propagate_coupled re-normalises quaternion at each output point."""
    state0 = make_initial_state(
        r_eci=[7000., 0., 0.], v_eci=[0., 7.5, 0.],
        omega=[0.5, 0.3, 0.1],  # large spin to stress integrator
    )
    cfg = CoupledStateConfig(inertia=INERTIA_SOYUZ)
    t, x = propagate_coupled(state0, (0.0, 300.0), cfg, t_eval=np.linspace(0, 300, 50))
    norms = np.linalg.norm(x[6:10, :], axis=0)
    assert np.allclose(norms, 1.0, atol=1e-12)


def test_thrust_with_attitude_rotates_thrust_to_eci():
    """Body-frame thrust should be rotated into ECI by the attitude quaternion.

    Uses baseline subtraction to isolate thrust effect from gravitational drift.
    """
    # 90-deg rotation about z: maps body-x to ECI-y
    q = np.array([0.0, 0.0, np.sin(np.pi/4), np.cos(np.pi/4)])
    state0 = make_initial_state(
        r_eci=[7000., 0., 0.], v_eci=[0., 7.5, 0.], quat=q,
    )
    def thrust_cb(t, x):
        return np.array([0.001, 0., 0.])  # body-x
    cfg_thrust = CoupledStateConfig(inertia=INERTIA_SOYUZ, thrust_callback=thrust_cb)
    cfg_baseline = CoupledStateConfig(inertia=INERTIA_SOYUZ)
    t1, x1 = propagate_coupled(state0, (0.0, 10.0), cfg_thrust, t_eval=np.array([0., 10.]), rtol=1e-11)
    t0, x0 = propagate_coupled(state0, (0.0, 10.0), cfg_baseline, t_eval=np.array([0., 10.]), rtol=1e-11)
    dv_thrust_only = x1[3:6, -1] - x0[3:6, -1]
    # 0.001 km/s² × 10 s = 0.01 km/s. Body-x → ECI-y under 90° z-rotation.
    assert dv_thrust_only[1] > 0.008          # ~10 mm/s gain in y (ECI)
    assert abs(dv_thrust_only[0]) < 1e-4      # negligible in ECI-x
    assert abs(dv_thrust_only[2]) < 1e-6      # negligible in ECI-z
