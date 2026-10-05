"""Two measurements the IAC-26 reviewers will ask for, and that §5.4 does not answer.

A. Constraint tightening. §5.4.1 swept horizon, step, per-impulse authority and the
   tracking weight, but held the terminal speed cap of (3.8) at 50 mm/s in all 81
   configurations — and §6 names that cap as the binding constraint. Here the cap
   given to the optimiser is backed off (50 -> 25 mm/s) while success is scored
   against the unchanged 50 mm/s requirement. This is the textbook route the paper
   cites and never ran, and it is the alternative the soft cost has to beat.

B. Dwell time. Success in §5 means being inside the capture envelope at t_f.
   Berthing needs the chaser to stay there while the arm closes. From each terminal
   state we propagate free drift (no control) with the HCW STM and record how long
   the chaser remains inside the ellipsoid.

Central cell only: 5 cm 3-sigma position noise, 100 ms latency, UKF upstream,
N = 30 steps of 10 s — the v3 calibration.

Output: experiments/results/tightening_dwell_<timestamp>.csv
"""
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path
import csv
import numpy as np

from oosim.proxops.hcw import mean_motion, hcw_state_transition_matrix
from oosim.targeting.envelope_specs import CANADARM2_BERTHING, NDS_DOCKING
from oosim.targeting.qp_targeting import qp_terminal_target
from oosim.targeting.ukf import UKFState, ukf_predict, ukf_update

N_TRIALS = 100
NOISE_3SIG = 0.05          # central cell
LATENCY = 0.10             # central cell
N_STEPS = 30
DT = 10.0
DV_MAX = 0.05
V_REQUIREMENT = CANADARM2_BERTHING.vel_max      # 50 mm/s — the real requirement
CAPS_MS = [50, 45, 40, 35, 30, 25]              # cap handed to the optimiser
DWELL_HORIZON_S = 300.0
DWELL_STEP_S = 1.0


def run_trial(args) -> dict:
    """One closed-loop trial. mode='hard' with a (possibly tightened) cap, or 'soft'."""
    seed, mode, cap = args
    rng = np.random.default_rng(seed)
    n = mean_motion(6378.137 + 408.0)
    target = CANADARM2_BERTHING.center_pos
    sigma_pos = NOISE_3SIG / 3.0
    sigma_vel = sigma_pos / 10.0
    R = np.eye(3) * (sigma_pos ** 2)
    Q = np.eye(6) * 1e-6

    true_state = np.array([10.0, -50.0, 0.0, 0.0, 0.0, 0.0])
    A_dt = hcw_state_transition_matrix(n, DT)

    init_meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
    estimate = UKFState(mean=np.concatenate([init_meas, [0.0, 0.0, 0.0]]),
                        cov=np.diag([sigma_pos**2 * 4]*3 + [sigma_vel**2 * 100]*3))

    kwargs = dict(terminal_mode="soft", lambda_terminal_pos=1000.0,
                  lambda_terminal_vel=1000.0) if mode == "soft" else {}
    cum_dv = 0.0
    for k in range(N_STEPS):
        meas = true_state[:3] + rng.normal(0, sigma_pos, 3)
        estimate = ukf_predict(estimate, n, LATENCY, Q)
        estimate = ukf_update(estimate, meas, R)

        remaining = N_STEPS - k
        if remaining < 1:  # apply every planned impulse, including the last
            break
        result = qp_terminal_target(
            initial_state=estimate.mean, target_pos=target, n=n,
            horizon_steps=remaining, dt=DT,
            capture_radius=CANADARM2_BERTHING.pos_semi_axes,
            v_max_terminal=cap, dv_max_per_step=DV_MAX, **kwargs)
        if not result.success:
            return {"feasible": False}
        first_dv = result.delta_vs[0]
        cum_dv += float(np.linalg.norm(first_dv))
        true_state[3:] += first_dv
        true_state = A_dt @ true_state
        estimate.mean[3:] += first_dv
        estimate = ukf_predict(estimate, n, DT, Q)

    rel = (true_state[:3] - target) / CANADARM2_BERTHING.pos_semi_axes
    inside_pos = float(np.dot(rel, rel)) <= 1.0
    speed = float(np.linalg.norm(true_state[3:]))
    return {
        "feasible": True,
        # scored against the UNCHANGED requirement, not against the tightened cap
        "success": bool(inside_pos and speed <= V_REQUIREMENT),
        "pos_err": float(np.linalg.norm(true_state[:3] - target)),
        "speed": speed,
        "dv": cum_dv,
        "dwell_canadarm2": dwell_time(true_state, target, CANADARM2_BERTHING.pos_semi_axes, n),
        "dwell_nds": dwell_time(true_state, target, NDS_DOCKING.pos_semi_axes, n),
    }


def dwell_time(state: np.ndarray, target: np.ndarray, semi_axes: np.ndarray, n: float) -> float:
    """Free-drift time (s) until the chaser leaves the ellipsoid. No control after t_f."""
    rel = (state[:3] - target) / semi_axes
    if float(np.dot(rel, rel)) > 1.0:
        return 0.0
    step = hcw_state_transition_matrix(n, DWELL_STEP_S)
    s = state.copy()
    for i in range(int(DWELL_HORIZON_S / DWELL_STEP_S)):
        s = step @ s
        rel = (s[:3] - target) / semi_axes
        if float(np.dot(rel, rel)) > 1.0:
            return (i + 1) * DWELL_STEP_S
    return DWELL_HORIZON_S  # still inside at the horizon


def summarise(tag: str, mode: str, cap: float, res: list) -> dict:
    ok = [r for r in res if r.get("feasible")]
    succ = [r for r in ok if r["success"]]
    arr = lambda key: np.array([r[key] for r in ok])
    return {
        "case": tag, "mode": mode, "cap_ms": cap * 1000, "requirement_ms": V_REQUIREMENT * 1000,
        "n_trials": len(res), "n_infeasible": len(res) - len(ok),
        "success_rate": len(succ) / len(res),
        "pos_err_p95_mm": float(np.percentile(arr("pos_err"), 95)) * 1000,
        "speed_p95_mms": float(np.percentile(arr("speed"), 95)) * 1000,
        "dv_mean_mms": float(arr("dv").mean()) * 1000,
        "dwell_canadarm2_median_s": float(np.median(arr("dwell_canadarm2"))),
        "dwell_canadarm2_p5_s": float(np.percentile(arr("dwell_canadarm2"), 5)),
        "dwell_nds_median_s": float(np.median(arr("dwell_nds"))),
        "dwell_nds_p5_s": float(np.percentile(arr("dwell_nds"), 5)),
    }


def main():
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"tightening_dwell_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.csv"

    cases = [(f"hard_cap_{c}mms", "hard", c / 1000.0) for c in CAPS_MS]
    cases.append(("soft_lambda1000", "soft", V_REQUIREMENT))

    rows = []
    with Pool() as pool:
        for tag, mode, cap in cases:
            jobs = [(1000 + i, mode, cap) for i in range(N_TRIALS)]
            res = pool.map(run_trial, jobs)
            row = summarise(tag, mode, cap, res)
            rows.append(row)
            print(f"  {tag:20s} success={row['success_rate']:6.1%}  "
                  f"p95_speed={row['speed_p95_mms']:6.1f} mm/s  "
                  f"dv={row['dv_mean_mms']:6.1f} mm/s  "
                  f"dwell(C2) median={row['dwell_canadarm2_median_s']:5.1f}s "
                  f"p5={row['dwell_canadarm2_p5_s']:5.1f}s  "
                  f"dwell(NDS) median={row['dwell_nds_median_s']:5.1f}s", flush=True)

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\nSaved {out_csv}")


if __name__ == "__main__":
    main()
