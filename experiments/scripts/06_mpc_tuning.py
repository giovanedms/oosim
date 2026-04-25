"""MPC parameter sweep — find a calibration that recovers >0% success.

The v1 closed-loop MPC at the original calibration (N=15 steps, dt=20 s,
dv_max=0.2 m/s, lambda_p=1.0) gave 0% success across the noise/latency grid.
This script sweeps the four calibration knobs to identify a setting that
achieves a useful trade-off between robustness and propellant cost.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target


N_TRIALS = 20
NOISE_3SIG = 0.05    # 5 cm
LATENCY = 0.10       # 100 ms
N = mean_motion(6378.137 + 408.0)


def trial(N_steps, dt, dv_max, lambda_p, rng) -> dict:
    sigma_pos = NOISE_3SIG / 3.0
    sigma_vel = sigma_pos / 10.0
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    target = CANADARM2_BERTHING.center_pos
    cum_dv = 0.0

    A_dt = hcw_state_transition_matrix(N, dt)

    for k in range(N_steps):
        meas = true_state.copy()
        meas[:3] += rng.normal(0, sigma_pos, 3)
        meas[3:] += rng.normal(0, sigma_vel, 3)
        meas[:3] += meas[3:] * LATENCY

        remaining = N_steps - k
        if remaining < 2:
            break
        result = qp_terminal_target(
            initial_state=meas, target_pos=target, n=N,
            horizon_steps=remaining, dt=dt,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=dv_max,
            lambda_pos=lambda_p,
        )
        if not result.success:
            return {"success": False, "pos_err": np.nan, "vel_norm": np.nan, "dv": np.nan}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        true_state = A_dt @ true_state

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
    rng = np.random.default_rng(0)
    sweep = []
    # Sweep over calibration grid
    configs = []
    for N_steps in [15, 30, 60]:
        for dt in [10.0, 20.0, 5.0]:
            for dv_max in [0.05, 0.10, 0.30]:
                for lam in [1.0, 10.0, 100.0]:
                    configs.append((N_steps, dt, dv_max, lam))
    print(f"Sweeping {len(configs)} configurations x {N_TRIALS} trials each "
          f"= {len(configs)*N_TRIALS} runs")

    for cfg in configs:
        Ns, dt, dvm, lam = cfg
        results = [trial(Ns, dt, dvm, lam, rng) for _ in range(N_TRIALS)]
        succ = [r for r in results if r["success"]]
        success_rate = len(succ) / len(results)
        if succ:
            mean_pos = float(np.mean([r["pos_err"] for r in succ]))
            mean_dv = float(np.mean([r["dv"] for r in succ]))
        else:
            all_pos = [r["pos_err"] for r in results if not np.isnan(r["pos_err"])]
            mean_pos = float(np.mean(all_pos)) if all_pos else float("nan")
            mean_dv = float("nan")
        sweep.append({
            "N_steps": Ns, "dt_s": dt, "dv_max_ms": dvm, "lambda_p": lam,
            "success_rate": success_rate,
            "mean_pos_err_m": mean_pos,
            "mean_dv_ms": mean_dv,
        })

    # Sort by success rate descending, then by dv ascending
    sweep_sorted = sorted(sweep, key=lambda r: (-r["success_rate"], r["mean_dv_ms"] or 1e9))
    print("\nTop 10 configurations by success rate (then by lower dv):")
    print(f"  {'N_steps':>7} {'dt[s]':>6} {'dv_max':>7} {'lambda':>6}  "
          f"{'success':>8} {'pos_err[mm]':>12} {'dv[mm/s]':>10}")
    for r in sweep_sorted[:10]:
        print(f"  {r['N_steps']:>7} {r['dt_s']:>6.1f} {r['dv_max_ms']:>7.2f} "
              f"{r['lambda_p']:>6.1f}  {r['success_rate']:>7.0%}  "
              f"{r['mean_pos_err_m']*1000:>11.1f}  "
              f"{r['mean_dv_ms']*1000 if r['mean_dv_ms']==r['mean_dv_ms'] else float('nan'):>10.1f}")

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_csv = out_dir / f"mpc_tuning_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sweep[0].keys())
        writer.writeheader()
        writer.writerows(sweep)
    print(f"\nFull sweep saved to {out_csv}")


if __name__ == "__main__":
    main()
