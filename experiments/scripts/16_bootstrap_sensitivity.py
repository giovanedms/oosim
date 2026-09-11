"""Bootstrap sensitivity at the central noise/latency cell.

100 trials at the central cell (5 cm noise, 100 ms latency) plus 30 trials at
each of the surrounding cells. From the 100-trial central sample we compute
1000-resample percentile-bootstrap 95% confidence intervals on the success
rate and the p95 terminal-pose error.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


N_STEPS = 30; DT = 10.0; DV_MAX = 0.05


def trial(noise_3sig, latency, n, target, rng):
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
        if remaining < 1: break  # apply every planned impulse, including the last
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=DV_MAX, terminal_mode="soft",
            lambda_terminal_pos=1000.0, lambda_terminal_vel=1000.0,
        )
        if not result.success:
            return {"success": False, "pos_err": np.nan}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        estimate.mean[3:] += first_dv
        true_state = A_dt @ true_state
        estimate = ukf_predict(estimate, n, DT, Q)
    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    pos_err = float(np.linalg.norm(true_state[:3] - target))
    inside = float(np.dot(rel, rel)) <= 1.0 and \
             float(np.linalg.norm(true_state[3:])) <= CANADARM2_BERTHING.vel_max
    return {"success": inside, "pos_err": pos_err}


def percentile_bootstrap(values, percentile, n_resample=1000, ci=95):
    rng = np.random.default_rng(0)
    arr = np.asarray(values)
    n = len(arr)
    if n == 0: return (float("nan"), float("nan"))
    samples = np.empty(n_resample)
    for i in range(n_resample):
        idx = rng.integers(0, n, size=n)
        samples[i] = np.percentile(arr[idx], percentile)
    lo = float(np.percentile(samples, (100 - ci) / 2))
    hi = float(np.percentile(samples, 100 - (100 - ci) / 2))
    return (lo, hi)


def clopper_pearson(k: int, n: int, alpha: float = 0.05):
    """Exact binomial confidence interval for success rate k/n."""
    from scipy.stats import beta
    if n == 0: return (0.0, 1.0)
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (lo, hi)


def main():
    rng = np.random.default_rng(99)
    n = mean_motion(6378.137 + 408.0)
    target = CANADARM2_BERTHING.center_pos

    # Central cell: 100 trials
    print("Central cell (5 cm noise, 100 ms latency): 100 trials with bootstrap CI")
    central_results = [trial(0.05, 0.10, n, target, rng) for _ in range(100)]
    n_succ = sum(r["success"] for r in central_results)
    pos_errs = [r["pos_err"] * 1000 for r in central_results]  # mm
    cp_lo, cp_hi = clopper_pearson(n_succ, 100)
    p95_lo, p95_hi = percentile_bootstrap(pos_errs, 95)
    print(f"  Success: {n_succ}/100  Clopper-Pearson 95% CI: [{cp_lo:.3f}, {cp_hi:.3f}]")
    print(f"  p95 pos err: {np.percentile(pos_errs, 95):.1f} mm  bootstrap 95% CI: [{p95_lo:.1f}, {p95_hi:.1f}] mm")
    print()

    # Surrounding cells: 30 trials each
    print("Surrounding cells (30 trials each):")
    rows = [{"noise_3sig_m": 0.05, "latency_s": 0.10, "n_trials": 100,
             "n_success": n_succ, "success_rate": n_succ / 100,
             "cp_lo": cp_lo, "cp_hi": cp_hi,
             "p95_pos_err_mm": float(np.percentile(pos_errs, 95)),
             "p95_lo_mm": p95_lo, "p95_hi_mm": p95_hi}]
    for noise in [0.005, 0.05, 0.20]:
        for lat in [0.05, 0.10, 0.20]:
            if noise == 0.05 and lat == 0.10: continue
            results = [trial(noise, lat, n, target, rng) for _ in range(30)]
            ns = sum(r["success"] for r in results)
            pe = [r["pos_err"] * 1000 for r in results]
            lo, hi = clopper_pearson(ns, 30)
            print(f"  noise={noise*1000:5.0f} mm  lat={lat*1000:3.0f} ms  "
                  f"success={ns}/30  CI=[{lo:.2f},{hi:.2f}]  p95_pos={np.percentile(pe,95):.1f} mm")
            rows.append({"noise_3sig_m": noise, "latency_s": lat, "n_trials": 30,
                         "n_success": ns, "success_rate": ns / 30,
                         "cp_lo": lo, "cp_hi": hi,
                         "p95_pos_err_mm": float(np.percentile(pe, 95)),
                         "p95_lo_mm": float("nan"), "p95_hi_mm": float("nan")})

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_csv = out_dir / f"bootstrap_sensitivity_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {out_csv}")


if __name__ == "__main__":
    main()
