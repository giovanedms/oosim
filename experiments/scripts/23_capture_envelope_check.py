"""Capture-envelope satisfaction margins for the 14-mission v3 validation.

Reads experiments/results/per_mission_v3.csv (script 14) and, for each
mission, computes how much margin the simulated terminal state has against
the capture envelope preset used in that run:

    pos_margin = (most restrictive semi-axis - pos_err) / semi-axis
    vel_margin = (vel_max - vel_norm) / vel_max

Output: experiments/results/capture_envelope_check.csv, referenced in
Section 5.5 of the IAC 2026 manuscript.
"""
from pathlib import Path
import csv

from oosim.targeting.envelope_specs import (
    CANADARM2_BERTHING, NDS_DOCKING, SSVP_DOCKING,
)

RESULTS = Path(__file__).resolve().parent.parent / "results"

ENVELOPES = {
    "CANADARM2_BERTHING": CANADARM2_BERTHING,
    "NDS_DOCKING": NDS_DOCKING,
    "SSVP_DOCKING": SSVP_DOCKING,
}


def envelope_from_name(env_name: str):
    """Resolve the envelope preset from the CSV column (strips ' (default)')."""
    key = env_name.replace(" (default)", "").strip()
    if key not in ENVELOPES:
        raise KeyError(f"unknown envelope preset in CSV: {env_name!r}")
    return ENVELOPES[key]


def main():
    in_csv = RESULTS / "per_mission_v3.csv"
    if not in_csv.exists():
        print("per_mission_v3.csv not found; run script 14 first.")
        return
    with open(in_csv) as f:
        missions = list(csv.DictReader(f))

    out_rows = []
    print(f"Capture-envelope margin check for {len(missions)} missions:")
    for r in missions:
        env = envelope_from_name(r["envelope_used"])
        pos_err_mm = float(r["terminal_pos_err_mm"])
        vel_mms = float(r["terminal_vel_norm_mm_s"])
        pos_bound_mm = float(env.pos_semi_axes.min()) * 1000.0
        vel_bound_mms = float(env.vel_max) * 1000.0
        pos_margin_pct = (pos_bound_mm - pos_err_mm) / pos_bound_mm * 100.0
        vel_margin_pct = (vel_bound_mms - vel_mms) / vel_bound_mms * 100.0
        out_rows.append({
            "mission": r["mission_id"],
            "envelope": r["envelope_used"],
            "pos_err_mm": round(pos_err_mm, 2),
            "pos_bound_mm": round(pos_bound_mm, 1),
            "pos_margin_pct": round(pos_margin_pct, 1),
            "vel_mms": round(vel_mms, 2),
            "vel_bound_mms": round(vel_bound_mms, 1),
            "vel_margin_pct": round(vel_margin_pct, 1),
        })
        print(f"  {r['mission_id']:25} pos {pos_err_mm:6.1f}/{pos_bound_mm:5.0f} mm "
              f"(margin {pos_margin_pct:5.1f}%)  vel {vel_mms:5.1f}/{vel_bound_mms:5.0f} mm/s "
              f"(margin {vel_margin_pct:5.1f}%)")

    out_csv = RESULTS / "capture_envelope_check.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_rows[0].keys())
        writer.writeheader()
        writer.writerows(out_rows)

    pos_margins = [r["pos_margin_pct"] for r in out_rows]
    vel_margins = [r["vel_margin_pct"] for r in out_rows]
    print()
    print(f"Saved {len(out_rows)} rows to {out_csv}")
    print(f"  pos margin: min={min(pos_margins):.1f}%  max={max(pos_margins):.1f}%")
    print(f"  vel margin: min={min(vel_margins):.1f}%  max={max(vel_margins):.1f}%")


if __name__ == "__main__":
    main()
