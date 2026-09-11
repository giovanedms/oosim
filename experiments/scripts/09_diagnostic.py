"""Diagnostic: isolate what's failing in the closed-loop MPC.

Runs 4 conditions to bisect the failure mode:
    A. Noise-free MPC, dv_max=0.2 (current default).
       If FAILS -> problem is in QP formulation/calibration, not noise.
    B. Noise-free MPC, dv_max=0.05, N_steps=30, dt=10s (gentler control).
       If WORKS where A fails -> control authority too aggressive.
    C. Noisy + UKF (50 mm 3-sigma, 100 ms latency), gentler control.
       If WORKS -> sweet spot found, just need better calibration.
    D. Single full-horizon QP (no MPC), noise-free.
       Should always work — sanity check that the QP solver itself is OK.

Output: console table + trajectory plot of one trial per condition.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


N_TRIALS = 20
n = mean_motion(6378.137 + 408.0)
target = CANADARM2_BERTHING.center_pos


def trial_noise_free_mpc(N_steps, dt, dv_max, capture_state_history=False):
    """Closed-loop MPC with PERFECT state knowledge."""
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, dt)
    cum_dv = 0.0
    history = [true_state.copy()] if capture_state_history else None
    for k in range(N_steps):
        remaining = N_steps - k
        if remaining < 1:  # apply every planned impulse, including the last
            break
        result = qp_terminal_target(
            initial_state=true_state, target_pos=target, n=n,
            horizon_steps=remaining, dt=dt,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=dv_max,
        )
        if not result.success:
            return {"success": False, "pos_err": np.nan, "vel_norm": np.nan,
                    "dv": np.nan, "history": history}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        true_state = A_dt @ true_state
        if capture_state_history:
            history.append(true_state.copy())

    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    inside_vel = float(np.linalg.norm(true_state[3:])) <= CANADARM2_BERTHING.vel_max
    return {
        "success": inside_pos and inside_vel,
        "pos_err": float(np.linalg.norm(true_state[:3] - target)),
        "vel_norm": float(np.linalg.norm(true_state[3:])),
        "dv": cum_dv,
        "history": history,
    }


def trial_noisy_with_ukf(N_steps, dt, dv_max, noise_3sig, latency, rng):
    """Same as noisy MC v2 but configurable parameters."""
    sigma_pos = noise_3sig / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, dt)

    init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
    init_mean = np.concatenate([init_meas, [0.0, 0.0, 0.0]])
    init_cov = np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3)
    estimate = UKFState(mean=init_mean, cov=init_cov)
    cum_dv = 0.0

    for k in range(N_steps):
        meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        estimate = ukf_predict(estimate, n, latency, Q)
        estimate = ukf_update(estimate, meas, R)
        remaining = N_steps - k
        if remaining < 1:  # apply every planned impulse, including the last
            break
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=dt,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=dv_max,
        )
        if not result.success:
            return {"success": False, "pos_err": np.nan, "vel_norm": np.nan, "dv": np.nan}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        estimate.mean[3:] += first_dv
        true_state = A_dt @ true_state
        estimate = ukf_predict(estimate, n, dt, Q)

    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    inside_vel = float(np.linalg.norm(true_state[3:])) <= CANADARM2_BERTHING.vel_max
    return {
        "success": inside_pos and inside_vel,
        "pos_err": float(np.linalg.norm(true_state[:3] - target)),
        "vel_norm": float(np.linalg.norm(true_state[3:])),
        "dv": cum_dv,
    }


def trial_full_horizon_qp(N_steps, dt, dv_max):
    """Single full-horizon QP, then apply ALL impulses to true state — sanity check."""
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    result = qp_terminal_target(
        initial_state=true_state, target_pos=target, n=n,
        horizon_steps=N_steps, dt=dt,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max,
        dv_max_per_step=dv_max,
    )
    if not result.success:
        return {"success": False, "pos_err": np.nan, "vel_norm": np.nan, "dv": np.nan}
    pos_err = float(np.linalg.norm(result.terminal_state[:3] - target))
    vel_norm = float(np.linalg.norm(result.terminal_state[3:]))
    rel = (result.terminal_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    inside_vel = vel_norm <= CANADARM2_BERTHING.vel_max
    return {
        "success": inside_pos and inside_vel,
        "pos_err": pos_err, "vel_norm": vel_norm,
        "dv": float(np.sum(np.linalg.norm(result.delta_vs, axis=1))),
    }


def main():
    rng = np.random.default_rng(0)
    print("=" * 78)
    print("DIAGNOSTIC: bisecting the closed-loop MPC failure mode")
    print("=" * 78)

    print("\n--- A. Noise-free MPC, default calibration (N=15, dt=20, dv=0.2) ---")
    res_a = [trial_noise_free_mpc(15, 20.0, 0.2) for _ in range(N_TRIALS)]
    print(f"  Success rate: {sum(r['success'] for r in res_a)/len(res_a):.0%}")
    print(f"  Mean pos err: {np.nanmean([r['pos_err'] for r in res_a])*1000:.1f} mm")
    print(f"  Mean vel norm: {np.nanmean([r['vel_norm'] for r in res_a])*1000:.1f} mm/s")

    print("\n--- B. Noise-free MPC, gentler (N=30, dt=10, dv=0.05) ---")
    res_b = [trial_noise_free_mpc(30, 10.0, 0.05) for _ in range(N_TRIALS)]
    print(f"  Success rate: {sum(r['success'] for r in res_b)/len(res_b):.0%}")
    print(f"  Mean pos err: {np.nanmean([r['pos_err'] for r in res_b])*1000:.1f} mm")
    print(f"  Mean vel norm: {np.nanmean([r['vel_norm'] for r in res_b])*1000:.1f} mm/s")

    print("\n--- C. Noisy (5 cm 3-sigma, 100 ms) + UKF, gentler (N=30, dt=10, dv=0.05) ---")
    res_c = [trial_noisy_with_ukf(30, 10.0, 0.05, 0.05, 0.1, rng) for _ in range(N_TRIALS)]
    print(f"  Success rate: {sum(r['success'] for r in res_c)/len(res_c):.0%}")
    print(f"  Mean pos err: {np.nanmean([r['pos_err'] for r in res_c])*1000:.1f} mm")
    print(f"  Mean vel norm: {np.nanmean([r['vel_norm'] for r in res_c])*1000:.1f} mm/s")

    print("\n--- D. Single full-horizon QP (no MPC), noise-free, gentler ---")
    res_d = [trial_full_horizon_qp(30, 10.0, 0.05) for _ in range(N_TRIALS)]
    print(f"  Success rate: {sum(r['success'] for r in res_d)/len(res_d):.0%}")
    print(f"  Mean pos err: {np.nanmean([r['pos_err'] for r in res_d])*1000:.1f} mm")
    print(f"  Mean vel norm: {np.nanmean([r['vel_norm'] for r in res_d])*1000:.1f} mm/s")

    # Plot one trajectory from condition A and one from condition B for comparison
    res_a_traj = trial_noise_free_mpc(15, 20.0, 0.2, capture_state_history=True)
    res_b_traj = trial_noise_free_mpc(30, 10.0, 0.05, capture_state_history=True)

    fig, axs = plt.subplots(1, 2, figsize=(8, 3.5))
    for ax, res, lbl in [(axs[0], res_a_traj, "A: N=15, dt=20, dv=0.2"),
                          (axs[1], res_b_traj, "B: N=30, dt=10, dv=0.05")]:
        h = np.array(res["history"])
        ax.plot(-h[:, 1], h[:, 0], "b-o", markersize=3, lw=0.7, label="chaser trajectory")
        # Capture envelope at target (10, 0, 0): semi 0.5 in x, 0.5 in y
        env = plt.Circle((0, 10), 0.5, fill=False, edgecolor="green", lw=1.0, label="envelope")
        ax.add_patch(env)
        ax.plot(0, 10, "g*", markersize=10, label="target")
        ax.set_xlabel("along-track distance to target [m]")
        ax.set_ylabel("R-bar [m]")
        ax.set_title(f"{lbl}\nfinal pos err: {res['pos_err']*1000:.0f} mm")
        ax.invert_xaxis()
        ax.legend(fontsize=7); ax.grid(alpha=0.3)

    fig.tight_layout()
    out = Path(__file__).resolve().parent.parent / "figures" / "fig_diagnostic.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\n  saved {out}")


if __name__ == "__main__":
    main()
