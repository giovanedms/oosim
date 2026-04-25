"""Monte Carlo robustness study: sensor noise + comm latency (v0, open-loop).

Runs the QP terminal targeting under varying levels of LIDAR range noise
and communication latency, with noise applied once to the initial state
plus a forward-propagation by the latency interval before solving the QP.

KNOWN LIMITATION (v0): this is an open-loop Monte Carlo — sensor noise enters
once, then the QP solves over the full horizon with perfect prediction. The
QP's predictive horizon makes it robust to single perturbations of the initial
state, so success rates approach 100% across the noise/latency grid tested.

A receding-horizon (MPC) Monte Carlo with noise re-injected at every step
will reveal the true degradation envelope and is planned for the A1 journal
extension. The IAC paper reports this v0 as a baseline.

Usage:
    python experiments/scripts/03_monte_carlo_noise.py
Output:
    experiments/results/monte_carlo_noise_<timestamp>.csv
"""
from datetime import datetime
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target


N_TRIALS_PER_CELL = 50
NOISE_LEVELS_3SIG_M = [0.005, 0.05, 0.20]    # 5 mm, 5 cm, 20 cm at 200 m range
LATENCY_LEVELS_S = [0.05, 0.10, 0.20]         # 50, 100, 200 ms


def perturb_state(state: np.ndarray, sigma_pos: float, sigma_vel: float, rng) -> np.ndarray:
    """Add Gaussian noise to position and velocity."""
    noisy = state.copy()
    noisy[:3] += rng.normal(0, sigma_pos, 3)
    noisy[3:] += rng.normal(0, sigma_vel, 3)
    return noisy


def run_trial(noise_3sig_m: float, latency_s: float, n: float, rng) -> dict:
    """Single MC trial: perturb initial state, propagate latency, solve QP."""
    sigma_pos = noise_3sig_m / 3.0
    sigma_vel = sigma_pos / 10.0
    initial_true = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    # Apply sensor noise to perceived state, then forward-propagate by latency
    initial_perceived = perturb_state(initial_true, sigma_pos, sigma_vel, rng)
    initial_after_latency = initial_perceived.copy()
    initial_after_latency[:3] += initial_perceived[3:] * latency_s

    result = qp_terminal_target(
        initial_state=initial_after_latency,
        target_pos=CANADARM2_BERTHING.center_pos,
        n=n,
        horizon_steps=15, dt=20.0,
        capture_radius=CANADARM2_BERTHING.pos_semi_axes,
        v_max_terminal=CANADARM2_BERTHING.vel_max,
        dv_max_per_step=0.2,
    )
    if not result.success:
        return {"success": False, "pos_error_m": np.nan, "vel_norm_ms": np.nan, "total_dv_ms": np.nan}

    pos_err = np.linalg.norm(result.terminal_state[:3] - CANADARM2_BERTHING.center_pos)
    vel_norm = np.linalg.norm(result.terminal_state[3:])
    total_dv = float(np.sum(np.linalg.norm(result.delta_vs, axis=1)))
    return {"success": True, "pos_error_m": pos_err, "vel_norm_ms": vel_norm,
            "total_dv_ms": total_dv}


def main():
    rng = np.random.default_rng(42)
    n = mean_motion(6378.137 + 408.0)
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"monte_carlo_noise_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.csv"

    rows = []
    print(f"Running {len(NOISE_LEVELS_3SIG_M)} x {len(LATENCY_LEVELS_S)} cells "
          f"x {N_TRIALS_PER_CELL} trials = "
          f"{len(NOISE_LEVELS_3SIG_M)*len(LATENCY_LEVELS_S)*N_TRIALS_PER_CELL} runs")

    for noise in NOISE_LEVELS_3SIG_M:
        for lat in LATENCY_LEVELS_S:
            results = [run_trial(noise, lat, n, rng) for _ in range(N_TRIALS_PER_CELL)]
            successes = [r for r in results if r["success"]]
            success_rate = len(successes) / len(results)
            if successes:
                pos_errs = np.array([r["pos_error_m"] for r in successes])
                pos_p95 = float(np.percentile(pos_errs, 95))
                pos_mean = float(pos_errs.mean())
                dv_mean = float(np.mean([r["total_dv_ms"] for r in successes]))
            else:
                pos_p95 = pos_mean = dv_mean = float("nan")
            row = {
                "noise_3sig_m": noise, "latency_s": lat,
                "n_trials": len(results),
                "success_rate": success_rate,
                "pos_err_p95_m": pos_p95,
                "pos_err_mean_m": pos_mean,
                "total_dv_mean_ms": dv_mean,
            }
            rows.append(row)
            print(f"  noise={noise*1000:5.0f} mm  latency={lat*1000:3.0f} ms  "
                  f"success={success_rate:.0%}  p95_pos_err={pos_p95*1e3:.1f} mm  "
                  f"mean_dv={dv_mean*1e3:.1f} mm/s")

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResults saved to {out_csv}")


if __name__ == "__main__":
    main()
