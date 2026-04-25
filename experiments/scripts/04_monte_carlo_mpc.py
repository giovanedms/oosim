"""Monte Carlo robustness study v1: MPC closed-loop with noise re-injection.

Improvement over v0 (script 03): instead of injecting noise once into the
initial state and solving the full-horizon QP open-loop, this version runs
the QP in receding-horizon (MPC) fashion. At each control step:

    1. Sensor measures the current relative state with Gaussian noise.
    2. After comm latency, the noisy estimate enters the QP solver.
    3. The QP solves over the remaining horizon and applies the FIRST impulse.
    4. The true state evolves under HCW dynamics.
    5. Repeat from step 1 at the next control step until the horizon ends.

This reveals the true noise/latency degradation envelope that the open-loop
v0 (script 03) cannot capture.

Output:
    experiments/results/monte_carlo_mpc_<timestamp>.csv
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target


N_TRIALS_PER_CELL = 30
NOISE_LEVELS_3SIG_M = [0.005, 0.05, 0.20]
LATENCY_LEVELS_S = [0.05, 0.10, 0.20]
N_STEPS = 15
DT = 20.0


def perturb_measurement(true_state: np.ndarray, sigma_pos: float, sigma_vel: float,
                         rng) -> np.ndarray:
    measured = true_state.copy()
    measured[:3] += rng.normal(0, sigma_pos, 3)
    measured[3:] += rng.normal(0, sigma_vel, 3)
    return measured


def run_mpc_trial(noise_3sig_m: float, latency_s: float, n: float, rng) -> dict:
    """Closed-loop MPC trial with noise re-injected at every control step."""
    sigma_pos = noise_3sig_m / 3.0
    sigma_vel = sigma_pos / 10.0

    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    target = CANADARM2_BERTHING.center_pos
    cum_dv = 0.0

    A_dt = hcw_state_transition_matrix(n, DT)
    B_dt = A_dt @ np.vstack([np.zeros((3, 3)), np.eye(3)])

    for k in range(N_STEPS):
        # 1) Measurement with noise
        measured = perturb_measurement(true_state, sigma_pos, sigma_vel, rng)
        # 2) Forward-propagate by latency (chaser thinks it sees state at t+latency)
        measured[:3] += measured[3:] * latency_s

        # 3) QP over remaining horizon
        remaining = N_STEPS - k
        if remaining < 2:
            break
        result = qp_terminal_target(
            initial_state=measured,
            target_pos=target,
            n=n,
            horizon_steps=remaining,
            dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=0.2,
        )
        if not result.success:
            return {"success": False, "pos_error_m": np.nan,
                    "vel_norm_ms": np.nan, "total_dv_ms": np.nan}

        # 4) Apply first impulse
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        # 5) Propagate true state by one step
        true_state = A_dt @ true_state

    pos_err = float(np.linalg.norm(true_state[:3] - target))
    vel_norm = float(np.linalg.norm(true_state[3:]))
    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_envelope = float(np.dot(rel, rel)) <= 1.0
    inside_velocity = vel_norm <= CANADARM2_BERTHING.vel_max
    success = inside_envelope and inside_velocity
    return {"success": success, "pos_error_m": pos_err,
            "vel_norm_ms": vel_norm, "total_dv_ms": cum_dv}


def main():
    rng = np.random.default_rng(123)
    n = mean_motion(6378.137 + 408.0)
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"monte_carlo_mpc_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"

    rows = []
    n_total = len(NOISE_LEVELS_3SIG_M) * len(LATENCY_LEVELS_S) * N_TRIALS_PER_CELL
    print(f"Running MPC closed-loop Monte Carlo: {n_total} trials "
          f"({len(NOISE_LEVELS_3SIG_M)}x{len(LATENCY_LEVELS_S)}x{N_TRIALS_PER_CELL})")

    for noise in NOISE_LEVELS_3SIG_M:
        for lat in LATENCY_LEVELS_S:
            results = [run_mpc_trial(noise, lat, n, rng) for _ in range(N_TRIALS_PER_CELL)]
            successes = [r for r in results if r["success"]]
            success_rate = len(successes) / len(results)
            all_pos = np.array([r["pos_error_m"] for r in results if not np.isnan(r["pos_error_m"])])
            all_vel = np.array([r["vel_norm_ms"] for r in results if not np.isnan(r["vel_norm_ms"])])
            all_dv = np.array([r["total_dv_ms"] for r in results if not np.isnan(r["total_dv_ms"])])
            row = {
                "noise_3sig_m": noise, "latency_s": lat,
                "n_trials": len(results),
                "success_rate": success_rate,
                "pos_err_p95_m": float(np.percentile(all_pos, 95)) if len(all_pos) > 0 else float("nan"),
                "pos_err_mean_m": float(all_pos.mean()) if len(all_pos) > 0 else float("nan"),
                "vel_norm_p95_ms": float(np.percentile(all_vel, 95)) if len(all_vel) > 0 else float("nan"),
                "total_dv_mean_ms": float(all_dv.mean()) if len(all_dv) > 0 else float("nan"),
            }
            rows.append(row)
            print(f"  noise={noise*1000:5.0f} mm  latency={lat*1000:3.0f} ms  "
                  f"success={success_rate:.0%}  p95_pos={row['pos_err_p95_m']*1e3:6.1f} mm  "
                  f"p95_vel={row['vel_norm_p95_ms']*1e3:6.1f} mm/s  mean_dv={row['total_dv_mean_ms']*1e3:.0f} mm/s")

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResults saved to {out_csv}")


if __name__ == "__main__":
    main()
