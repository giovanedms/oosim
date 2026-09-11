"""Test the soft-terminal-cost MPC fix against the v1/v2 negative result."""
from datetime import datetime, timezone
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


N_TRIALS = 30
NOISE_LEVELS = [0.005, 0.05, 0.20]
LATENCY_LEVELS = [0.05, 0.10, 0.20]
N_STEPS = 30
DT = 10.0
DV_MAX = 0.05


def run_trial(noise_3sig, latency, n, target, rng, use_ukf=True):
    sigma_pos = noise_3sig / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, DT)

    if use_ukf:
        init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        init_mean = np.concatenate([init_meas, [0.0, 0.0, 0.0]])
        init_cov = np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3)
        estimate = UKFState(mean=init_mean, cov=init_cov)

    cum_dv = 0.0
    for k in range(N_STEPS):
        if use_ukf:
            meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
            estimate = ukf_predict(estimate, n, latency, Q)
            estimate = ukf_update(estimate, meas, R)
            qp_input = estimate.mean
        else:
            qp_input = true_state.copy()
            qp_input[:3] += rng.normal(0, sigma_pos, 3)
            qp_input[3:] += rng.normal(0, sigma_vel, 3)
            qp_input[:3] += qp_input[3:] * latency

        remaining = N_STEPS - k
        if remaining < 1:  # apply every planned impulse, including the last
            break
        result = qp_terminal_target(
            initial_state=qp_input, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=DV_MAX,
            terminal_mode="soft",
            lambda_terminal_pos=1000.0,
            lambda_terminal_vel=1000.0,
        )
        if not result.success:
            return {"success": False, "pos_err": np.nan, "vel_norm": np.nan, "dv": np.nan}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        true_state = A_dt @ true_state
        if use_ukf:
            estimate.mean[3:] += first_dv
            estimate = ukf_predict(estimate, n, DT, Q)

    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    inside_vel = float(np.linalg.norm(true_state[3:])) <= CANADARM2_BERTHING.vel_max
    return {
        "success": inside_pos and inside_vel,
        "pos_err": float(np.linalg.norm(true_state[:3] - target)),
        "vel_norm": float(np.linalg.norm(true_state[3:])),
        "dv": cum_dv,
    }


def main():
    rng = np.random.default_rng(11)
    n = mean_motion(6378.137 + 408.0)
    target = CANADARM2_BERTHING.center_pos

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"monte_carlo_soft_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"

    rows = []
    print(f"Running soft-terminal MPC + UKF Monte Carlo: "
          f"{len(NOISE_LEVELS)*len(LATENCY_LEVELS)*N_TRIALS} trials")
    print(f"  Calibration: N_steps={N_STEPS}, dt={DT}s, dv_max={DV_MAX} m/s, lambda_terminal=1000")

    for noise in NOISE_LEVELS:
        for lat in LATENCY_LEVELS:
            results = [run_trial(noise, lat, n, target, rng, use_ukf=True) for _ in range(N_TRIALS)]
            successes = [r for r in results if r["success"]]
            success_rate = len(successes) / len(results)
            all_pos = np.array([r["pos_err"] for r in results if not np.isnan(r["pos_err"])])
            all_vel = np.array([r["vel_norm"] for r in results if not np.isnan(r["vel_norm"])])
            all_dv = np.array([r["dv"] for r in results if not np.isnan(r["dv"])])
            row = {
                "noise_3sig_m": noise, "latency_s": lat, "n_trials": len(results),
                "success_rate": success_rate,
                "pos_err_p95_m": float(np.percentile(all_pos, 95)) if len(all_pos) > 0 else float("nan"),
                "pos_err_mean_m": float(all_pos.mean()) if len(all_pos) > 0 else float("nan"),
                "vel_norm_p95_ms": float(np.percentile(all_vel, 95)) if len(all_vel) > 0 else float("nan"),
                "total_dv_mean_ms": float(all_dv.mean()) if len(all_dv) > 0 else float("nan"),
            }
            rows.append(row)
            print(f"  noise={noise*1000:5.0f} mm  lat={lat*1000:3.0f} ms  "
                  f"success={success_rate:.0%}  p95_pos={row['pos_err_p95_m']*1e3:7.1f} mm  "
                  f"p95_vel={row['vel_norm_p95_ms']*1e3:6.1f} mm/s  "
                  f"mean_dv={row['total_dv_mean_ms']*1e3:.0f} mm/s")

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResults saved to {out_csv}")


if __name__ == "__main__":
    main()
