"""V-bar corridor compliance of the v3 pipeline under noise (central cell).

Re-runs the v3 MPC trial of scripts 10/18 at the central Monte Carlo cell
(5 cm 3-sigma position noise, 100 ms latency, N=30 steps, dt=10 s,
dv_max=0.05 m/s, soft terminal cost lambda_T=1000, UKF in the loop,
seed 11), recording the TRUE trajectory of every trial and checking each
step against the approach corridor of oosim.proxops.vbar:

    |x| <= 0.10*|y| + 5 m      (radial, R-bar)
    |z| <= 0.05*|y| + 3 m      (cross-track, H-bar)

LVLH convention: y = along-track approach axis (chaser starts at
[10, -50, 0] m, i.e. exactly ON the radial corridor boundary at |y|=50 m).
Because of that borderline start, compliance is also reported counting
from the 2nd trajectory point onward.

NOTE: the corridor cone of vbar.py is centred on the LVLH origin, while the
CANADARM2 berthing box centre sits at +10 m R-bar; a target-centred variant
(|x - x_tgt| <= 0.10*|y| + 5) is therefore reported alongside the raw check.

Output: experiments/results/vbar_compliance_<timestamp>.csv (one row per
trial) + aggregate numbers printed to stdout.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.proxops.vbar import vbar_corridor_bounds
from oosim.targeting.envelope_specs import CANADARM2_BERTHING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update


N_TRIALS = 200
NOISE_3SIG = 0.05   # 5 cm, central cell
LATENCY = 0.10      # 100 ms, central cell
N_STEPS = 30
DT = 10.0
DV_MAX = 0.05
SEED = 11


def run_trial(n, target, rng) -> np.ndarray | None:
    """One v3 closed-loop trial (script 10 mechanism); returns true trajectory."""
    sigma_pos = NOISE_3SIG / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6
    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, DT)

    init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
    init_mean = np.concatenate([init_meas, [0.0, 0.0, 0.0]])
    init_cov = np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3)
    estimate = UKFState(mean=init_mean, cov=init_cov)

    traj = [true_state.copy()]
    for k in range(N_STEPS):
        meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        estimate = ukf_predict(estimate, n, LATENCY, Q)
        estimate = ukf_update(estimate, meas, R)
        remaining = N_STEPS - k
        if remaining < 2:
            break
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=CANADARM2_BERTHING.vel_max,
            dv_max_per_step=DV_MAX,
            terminal_mode="soft",
            lambda_terminal_pos=1000.0,
            lambda_terminal_vel=1000.0,
        )
        if not result.success:
            return None
        first_dv = result.delta_vs[0]
        true_state[3:] += first_dv
        true_state = A_dt @ true_state
        estimate.mean[3:] += first_dv
        estimate = ukf_predict(estimate, n, DT, Q)
        traj.append(true_state.copy())
    return np.asarray(traj)


def corridor_metrics(traj: np.ndarray, x_target: float) -> dict:
    """Per-step corridor check (raw and target-centred) over one trajectory."""
    n_steps = len(traj)
    raw_ok = np.zeros(n_steps, dtype=bool)
    ctr_ok = np.zeros(n_steps, dtype=bool)
    worst = 0.0
    worst_step = 0
    for i, s in enumerate(traj):
        x, y, z = s[0], s[1], s[2]
        xb, zb = vbar_corridor_bounds(y)
        raw_ok[i] = abs(x) <= xb and abs(z) <= zb
        ctr_ok[i] = abs(x - x_target) <= xb and abs(z) <= zb
        violation = max(abs(x) - xb, abs(z) - zb, 0.0)
        if violation > worst:
            worst, worst_step = violation, i
    return {
        "n_steps": n_steps,
        "n_compliant_raw": int(raw_ok.sum()),
        "compliant_all_raw": bool(raw_ok.all()),
        "compliant_from_step2_raw": bool(raw_ok[1:].all()),
        "n_compliant_centered": int(ctr_ok.sum()),
        "compliant_all_centered": bool(ctr_ok.all()),
        "worst_violation_m": worst,
        "worst_violation_step": worst_step,
    }


def main():
    rng = np.random.default_rng(SEED)
    n = mean_motion(6378.137 + 408.0)
    target = CANADARM2_BERTHING.center_pos

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_csv = out_dir / f"vbar_compliance_{ts}.csv"

    print(f"V-bar corridor compliance: {N_TRIALS} v3 trials at central cell "
          f"(noise={NOISE_3SIG*1000:.0f} mm 3-sigma, latency={LATENCY*1000:.0f} ms, seed={SEED})")
    print(f"  Calibration: N_steps={N_STEPS}, dt={DT}s, dv_max={DV_MAX} m/s, lambda_T=1000, UKF on")

    rows = []
    n_qp_failures = 0
    for trial in range(N_TRIALS):
        traj = run_trial(n, target, rng)
        if traj is None:
            n_qp_failures += 1
            continue
        m = corridor_metrics(traj, x_target=float(target[0]))
        m["trial"] = trial
        m["final_pos_err_mm"] = float(np.linalg.norm(traj[-1][:3] - target)) * 1000
        rows.append(m)
        if (trial + 1) % 50 == 0:
            print(f"  ... {trial + 1}/{N_TRIALS} trials done")

    fieldnames = ["trial", "n_steps", "n_compliant_raw", "compliant_all_raw",
                  "compliant_from_step2_raw", "n_compliant_centered",
                  "compliant_all_centered", "worst_violation_m",
                  "worst_violation_step", "final_pos_err_mm"]
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_steps = sum(r["n_steps"] for r in rows)
    raw_steps = sum(r["n_compliant_raw"] for r in rows)
    ctr_steps = sum(r["n_compliant_centered"] for r in rows)
    n_all_raw = sum(r["compliant_all_raw"] for r in rows)
    n_from2_raw = sum(r["compliant_from_step2_raw"] for r in rows)
    n_all_ctr = sum(r["compliant_all_centered"] for r in rows)
    worst = max(r["worst_violation_m"] for r in rows)

    print()
    print(f"Saved {len(rows)} trial rows to {out_csv} ({n_qp_failures} QP failures)")
    print("Raw corridor |x| <= 0.10|y|+5, |z| <= 0.05|y|+3 (origin-centred):")
    print(f"  trials 100% compliant:            {n_all_raw}/{len(rows)} ({n_all_raw/len(rows):.1%})")
    print(f"  trials compliant from 2nd step:   {n_from2_raw}/{len(rows)} ({n_from2_raw/len(rows):.1%})")
    print(f"  compliant steps overall:          {raw_steps}/{total_steps} ({raw_steps/total_steps:.1%})")
    print(f"  worst violation:                  {worst:.3f} m")
    print("Target-centred corridor |x - x_tgt| <= 0.10|y|+5 (berthing box at +10 m R-bar):")
    print(f"  trials 100% compliant:            {n_all_ctr}/{len(rows)} ({n_all_ctr/len(rows):.1%})")
    print(f"  compliant steps overall:          {ctr_steps}/{total_steps} ({ctr_steps/total_steps:.1%})")


if __name__ == "__main__":
    main()
