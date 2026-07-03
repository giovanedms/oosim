"""Failure-boundary sweep for the v3 controller — push past the plausible envelope.

Reviewer question the paper must pre-empt: the 9-cell operational sweep
(script 18) reports 100% capture success across 5--200 mm sensor noise and
50--200 ms latency, so the failure boundary is never observed. This script
extends the grid far beyond any realistic rendezvous sensor (up to 1.5 m of
3-sigma relative-position noise and 2 s of estimator latency) to locate the
knee where soft-terminal-cost v3 finally degrades below 100%.

Same trial kernel as 18_statistical_sweep_parallel.py (soft terminal QP + UKF,
N=30, dt=10 s, dv_max=0.05, CANADARM2 berthing box). Output:
experiments/results/failure_boundary_<timestamp>.csv with Clopper-Pearson
success-rate CIs and bootstrap p95 terminal-error CIs per cell.
"""
from datetime import datetime, timezone
from pathlib import Path
from multiprocessing import Pool
import csv
import os
import numpy as np


N_TRIALS_PER_CELL = 400
# Sensor 3-sigma position noise, in metres. Realistic RVS/lidar is cm-level;
# the last three columns (0.6--1.5 m) are deliberately unphysical to bracket
# the boundary from both sides.
NOISE_LEVELS = [0.05, 0.20, 0.40, 0.60, 0.80, 1.00, 1.50]
# Estimator/actuation latency, seconds. 2 s is ~20x a typical GNC cycle.
LATENCY_LEVELS = [0.10, 0.50, 1.00, 2.00]
N_STEPS = 30
DT = 10.0
DV_MAX = 0.05


def trial_single(args):
    """Single trial — module-level for multiprocessing pickling.

    Identical kernel to script 18 so the two sweeps are directly comparable;
    only the (noise, latency) grid differs.
    """
    noise_3sig, latency, seed = args
    from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
    from oosim.targeting.envelope_specs import CANADARM2_BERTHING
    from oosim.targeting.qp_targeting import qp_terminal_target
    from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update

    rng = np.random.default_rng(seed)
    n = mean_motion(6378.137 + 408.0)
    target = CANADARM2_BERTHING.center_pos
    sigma_pos = noise_3sig / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, DT)
    init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
    init_mean = np.concatenate([init_meas, [0., 0., 0.]])
    init_cov = np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3)
    estimate = UKFState(mean=init_mean, cov=init_cov)
    cum_dv = 0.0
    for k in range(N_STEPS):
        meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        estimate = ukf_predict(estimate, n, latency, Q)
        estimate = ukf_update(estimate, meas, R)
        remaining = N_STEPS - k
        if remaining < 2:
            break
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=DV_MAX, terminal_mode="soft",
            lambda_terminal_pos=1000.0, lambda_terminal_vel=1000.0,
        )
        if not result.success:
            return (False, np.nan, np.nan, np.nan)
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        estimate.mean[3:] += first_dv
        true_state = A_dt @ true_state
        estimate = ukf_predict(estimate, n, DT, Q)
    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    pos_err = float(np.linalg.norm(true_state[:3] - target))
    vel_norm = float(np.linalg.norm(true_state[3:]))
    inside = float(np.dot(rel, rel)) <= 1.0 and vel_norm <= CANADARM2_BERTHING.vel_max
    return (inside, pos_err, vel_norm, cum_dv)


def percentile_bootstrap(values, percentile, n_resample=1000, ci=95):
    rng = np.random.default_rng(0)
    arr = np.asarray(values)
    n = len(arr)
    if n == 0:
        return (float("nan"), float("nan"))
    samples = np.empty(n_resample)
    for i in range(n_resample):
        idx = rng.integers(0, n, size=n)
        samples[i] = np.percentile(arr[idx], percentile)
    return float(np.percentile(samples, (100 - ci) / 2)), \
        float(np.percentile(samples, 100 - (100 - ci) / 2))


def clopper_pearson(k, n, alpha=0.05):
    from scipy.stats import beta
    if n == 0:
        return (0.0, 1.0)
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (float(lo), float(hi))


def main():
    n_cores = max(1, os.cpu_count() - 2)
    total = len(NOISE_LEVELS) * len(LATENCY_LEVELS) * N_TRIALS_PER_CELL
    print(f"Failure-boundary sweep: {total} trials across {n_cores} cores")

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"failure_boundary_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"

    rows = []
    for noise in NOISE_LEVELS:
        for lat in LATENCY_LEVELS:
            seeds = [(noise, lat, 100000 * int(noise * 10000) + 1000 * int(lat * 1000) + s)
                     for s in range(N_TRIALS_PER_CELL)]
            with Pool(n_cores) as pool:
                results = pool.map(trial_single, seeds)
            successes = [r for r in results if r[0]]
            success_rate = len(successes) / len(results)
            cp_lo, cp_hi = clopper_pearson(len(successes), len(results))
            pos_errs_mm = [r[1] * 1000 for r in results if not np.isnan(r[1])]
            p95 = float(np.percentile(pos_errs_mm, 95)) if pos_errs_mm else float("nan")
            p95_lo, p95_hi = percentile_bootstrap(pos_errs_mm, 95)
            # QP infeasibility count: trials that returned NaN pos error.
            n_qp_fail = sum(1 for r in results if np.isnan(r[1]))
            row = {
                "noise_3sig_m": noise, "latency_s": lat, "n_trials": N_TRIALS_PER_CELL,
                "n_success": len(successes), "success_rate": success_rate,
                "cp_lo": cp_lo, "cp_hi": cp_hi,
                "n_qp_infeasible": n_qp_fail,
                "p95_pos_err_mm": p95, "p95_lo_mm": p95_lo, "p95_hi_mm": p95_hi,
                "mean_pos_err_mm": float(np.mean(pos_errs_mm)) if pos_errs_mm else float("nan"),
            }
            rows.append(row)
            print(f"  noise={noise*1000:6.0f} mm  lat={lat*1000:4.0f} ms  "
                  f"success={len(successes)}/{N_TRIALS_PER_CELL} CI=[{cp_lo:.3f},{cp_hi:.3f}]  "
                  f"qp_fail={n_qp_fail}  p95_pos={p95:.1f} mm")

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {out_csv}")

    # Locate the boundary: highest noise level that holds 100% at every latency,
    # and the worst-case cell overall.
    by_noise = {}
    for r in rows:
        by_noise.setdefault(r["noise_3sig_m"], []).append(r["success_rate"])
    full = [nz for nz, rates in sorted(by_noise.items()) if min(rates) >= 1.0]
    worst = min(rows, key=lambda r: r["success_rate"])
    print(f"100%-across-all-latency up to noise 3sigma = {max(full)*1000:.0f} mm"
          if full else "No noise level held 100% across all latencies")
    print(f"Worst cell: noise={worst['noise_3sig_m']*1000:.0f} mm "
          f"lat={worst['latency_s']*1000:.0f} ms -> success_rate={worst['success_rate']:.3f}")


if __name__ == "__main__":
    main()
