"""Generate validation_summary.csv: one row per hardcoded mission.

Cross-references the 11 mission parsers with the v3 simulator to produce a
unified validation table that can be cited in Section 5.2 of the paper.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv

from oosim.missions import ALL_MISSIONS


def main():
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "validation_summary.csv"
    rows = []
    for m in ALL_MISSIONS:
        sum_burn_dv = sum(b.delta_v_ms for b in m.burns)
        rows.append({
            "mission_id": m.mission_id,
            "year": m.launch_utc[:4],
            "agency_country": m.target_port[:30],
            "type": "berthing" if "Canadarm" in m.capture_mechanism else "docking",
            "L2D_h": round(m.launch_to_dock_min / 60.0, 2),
            "profile_orbits": m.profile_orbits,
            "n_burns_documented": len(m.burns),
            "burn_dv_sum_ms": round(sum_burn_dv, 2),
            "published_total_dv_ms": round(m.total_dv_ms, 2),
            "dv_replay_consistency": "exact" if abs(sum_burn_dv - m.total_dv_ms) < 1.0 else "aggregate-only",
            "gnc_system": m.gnc_system[:60],
            "capture_mechanism": m.capture_mechanism[:60],
            "granularity": m.granularity,
            "primary_doi": m.primary_doi or "",
            "primary_url": m.primary_url[:80],
        })

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} mission rows to {out_csv}")
    print()
    print("Summary:")
    for r in rows:
        print(f"  {r['mission_id']:25} {r['year']} L2D={r['L2D_h']:>7.1f} h  "
              f"burns={r['n_burns_documented']}  dv={r['burn_dv_sum_ms']:>7.1f} m/s  "
              f"granularity={r['granularity']}")


if __name__ == "__main__":
    main()
