"""End-to-end replay of Soyuz MS-17 with the v3 calibration.

Replays the published Murtazin burn sequence (3 phasing burns), then runs
the v3 (UKF + soft-terminal MPC) terminal targeting from the post-phasing
hold point through capture.

Output: experiments/results/soyuz_ms17_full_<timestamp>.json
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np

from oosim.missions import SOYUZ_MS17
from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import SSVP_DOCKING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


N_TERMINAL_STEPS = 30
DT_TERMINAL = 10.0
DV_MAX = 0.05
NOISE_3SIG = 0.05  # 5 cm
LATENCY = 0.10     # 100 ms


def main():
    rng = np.random.default_rng(2026)
    n = mean_motion(6378.137 + 408.0)

    print("=" * 78)
    print(f"END-TO-END REPLAY: {SOYUZ_MS17.mission_id}")
    print("=" * 78)
    print(f"Source: Murtazin et al. 2020 Acta Astro DOI {SOYUZ_MS17.primary_doi}")
    print(f"Profile: {SOYUZ_MS17.profile_orbits}-orbit ultra-rapid")
    print(f"Published L2D: {SOYUZ_MS17.launch_to_dock_min:.2f} min")
    print()

    # --- 1) Replay published burn sequence ---
    print("Phase 1 — Phasing burns (open-loop replay):")
    total_dv_phasing = 0.0
    for b in SOYUZ_MS17.burns:
        print(f"  T+{b.t_from_launch_min:5.1f} min  {b.name:5} dv={b.delta_v_ms:.2f} m/s  ({b.notes})")
        total_dv_phasing += b.delta_v_ms
    print(f"  TOTAL phasing dv: {total_dv_phasing:.2f} m/s vs published "
          f"{SOYUZ_MS17.total_dv_ms:.1f} m/s (diff {abs(total_dv_phasing - SOYUZ_MS17.total_dv_ms):.2f})")
    print()

    # --- 2) Terminal phase with v3 (UKF + soft + gentler MPC) ---
    print("Phase 2 — Terminal targeting (v3: UKF + soft + gentler MPC):")
    print(f"  Calibration: N={N_TERMINAL_STEPS}, dt={DT_TERMINAL}s, dv_max={DV_MAX} m/s")
    print(f"  Sensor noise 3-sigma: {NOISE_3SIG*100:.1f} cm; latency: {LATENCY*1000:.0f} ms")

    target = SSVP_DOCKING.center_pos
    A_dt = hcw_state_transition_matrix(n, DT_TERMINAL)

    # Start of terminal phase: chaser ~50 m behind ISS Rassvet on V-bar after Murtazin DV3
    true_state = np.array([0.0, -50.0, 0.0, 0.0, 0.0, 0.0])

    # Initialize UKF
    sigma_pos = NOISE_3SIG / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6
    init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
    init_mean = np.concatenate([init_meas, [0., 0., 0.]])
    init_cov = np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3)
    estimate = UKFState(mean=init_mean, cov=init_cov)

    cum_dv_terminal = 0.0
    trajectory = [true_state.copy()]
    estimates = [estimate.mean.copy()]

    for k in range(N_TERMINAL_STEPS):
        meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        estimate = ukf_predict(estimate, n, LATENCY, Q)
        estimate = ukf_update(estimate, meas, R)

        remaining = N_TERMINAL_STEPS - k
        if remaining < 1:  # apply every planned impulse, including the last
            break
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT_TERMINAL,
            capture_radius=SSVP_DOCKING.pos_semi_axes,
            v_max_terminal=SSVP_DOCKING.vel_max,
            dv_max_per_step=DV_MAX,
            terminal_mode="soft", lambda_terminal_pos=1000.0, lambda_terminal_vel=1000.0,
        )
        if not result.success:
            print(f"  Step {k}: QP failed: {result.solver_status}"); break
        first_dv = result.delta_vs[0]
        cum_dv_terminal += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        estimate.mean[3:] += first_dv
        true_state = A_dt @ true_state
        estimate = ukf_predict(estimate, n, DT_TERMINAL, Q)
        trajectory.append(true_state.copy())
        estimates.append(estimate.mean.copy())

    pos_err = float(np.linalg.norm(true_state[:3] - target))
    vel_norm = float(np.linalg.norm(true_state[3:]))
    rel = (true_state[:3] - target) / SSVP_DOCKING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    inside_vel = vel_norm <= SSVP_DOCKING.vel_max

    print(f"  Terminal pos: {true_state[:3].round(3)} m  (err {pos_err*1000:.1f} mm)")
    print(f"  Terminal vel: {true_state[3:].round(3)} m/s  (norm {vel_norm*1000:.1f} mm/s)")
    print(f"  Inside SSVP envelope: pos={inside_pos}, vel={inside_vel}")
    print(f"  Terminal phase total dv: {cum_dv_terminal*1000:.1f} mm/s  ({len(trajectory)-1} impulses)")
    print()
    print("=" * 78)
    print("AGGREGATE VALIDATION:")
    print(f"  Phasing dv (replayed):   {total_dv_phasing:.2f} m/s")
    print(f"  Terminal dv (simulated): {cum_dv_terminal*1000:.1f} mm/s = {cum_dv_terminal:.3f} m/s")
    print(f"  TOTAL OOSim dv:          {total_dv_phasing + cum_dv_terminal:.3f} m/s")
    print(f"  Published total dv:      {SOYUZ_MS17.total_dv_ms:.1f} m/s")
    print(f"  L2D published:           {SOYUZ_MS17.launch_to_dock_min:.2f} min")
    print(f"  Terminal phase duration: {(N_TERMINAL_STEPS * DT_TERMINAL)/60:.1f} min")
    print("=" * 78)

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"soyuz_ms17_full_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    summary = {
        "mission_id": SOYUZ_MS17.mission_id,
        "phasing_dv_replayed_ms": total_dv_phasing,
        "terminal_dv_simulated_ms": cum_dv_terminal,
        "total_dv_ms": total_dv_phasing + cum_dv_terminal,
        "published_total_dv_ms": SOYUZ_MS17.total_dv_ms,
        "terminal_pos_error_mm": pos_err * 1000,
        "terminal_vel_norm_mm_s": vel_norm * 1000,
        "inside_envelope_pos": inside_pos,
        "inside_envelope_vel": inside_vel,
        "calibration": {"N_steps": N_TERMINAL_STEPS, "dt_s": DT_TERMINAL,
                        "dv_max_ms": DV_MAX, "noise_3sig_m": NOISE_3SIG, "latency_s": LATENCY},
        "primary_doi": SOYUZ_MS17.primary_doi,
        "trajectory_summary": {
            "n_impulses": len(trajectory) - 1,
            "duration_min": (N_TERMINAL_STEPS * DT_TERMINAL) / 60,
        }
    }
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to {out_json}")


if __name__ == "__main__":
    main()
