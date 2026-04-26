"""Generate a single FINAL_SUMMARY.md aggregating all results for the paper.

Reads the latest CSVs from experiments/results/ and the manuscript section
files, and produces a top-level summary at experiments/FINAL_SUMMARY.md
suitable for inclusion in the GitHub release notes and as the headline
content for the Zenodo dataset README.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv

EXP = Path(__file__).resolve().parent.parent
RESULTS = EXP / "results"
OUT = EXP / "FINAL_SUMMARY.md"


def latest(pattern: str) -> Path | None:
    files = sorted(RESULTS.glob(pattern))
    return files[-1] if files else None


def read_csv(p: Path):
    with open(p) as f:
        return list(csv.DictReader(f))


def main():
    sweep = latest("statistical_sweep_*.csv")
    per_miss = RESULTS / "per_mission_v3.csv"
    soyuz = latest("soyuz_ms17_full_*.json")

    out_lines = [
        "# OOSim — Final Headline Results Summary",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "Companion summary for the IAC 2026 paper `IAC-26,C2,3,6,x112752` and",
        "the OOSim release on `github.com/giovanedms/oosim`.",
        "",
        "## v0 → v3 architectural cascade",
        "",
        "| Version | Description | Success rate | p95 pos err |",
        "|---|---|---|---|",
        "| v0 | Open-loop QP single-shot (cosmetic) | 100% | 0.4 mm |",
        "| v1 | Closed-loop MPC, hard terminal | **0%** | 1080 mm |",
        "| v2 | UKF + closed-loop MPC, hard terminal | **0%** | 1027 mm |",
        "| v3 | UKF + soft terminal cost + gentler control | **100%** | 12-153 mm |",
        "",
        "Architectural lesson: hard terminal constraints in receding-horizon MPC ",
        "cause sub-optimization (each iteration commits to a plan it discards). ",
        "Soft terminal cost replaces the constraint with a quadratic penalty, ",
        "allowing intermediate states to hover near the envelope while the ",
        "multiplicity of MPC iterations drives convergence inside.",
        "",
    ]

    if sweep is not None:
        out_lines.append("## Statistical sensitivity (v3, 500 trials per cell, parallel)")
        out_lines.append("")
        out_lines.append("| 3σ noise [mm] | latency [ms] | success | CI lower | p95 pos [mm] | bootstrap CI |")
        out_lines.append("|---|---|---|---|---|---|")
        for r in read_csv(sweep):
            out_lines.append(
                f"| {float(r['noise_3sig_m'])*1000:.0f} | "
                f"{float(r['latency_s'])*1000:.0f} | "
                f"{int(float(r['n_success']))}/{int(float(r['n_trials']))} | "
                f"{float(r['cp_lo']):.3f} | "
                f"{float(r['p95_pos_err_mm']):.1f} | "
                f"[{float(r['p95_lo_mm']):.1f}, {float(r['p95_hi_mm']):.1f}] |"
            )
        out_lines.append("")

    if per_miss.exists():
        out_lines.append("## Per-mission validation (v3 pipeline, 11 hardcoded missions)")
        out_lines.append("")
        out_lines.append("| Mission | Sim total dv [m/s] | Pub total dv [m/s] | Rel err [%] | Pos err [mm] | Inside env? |")
        out_lines.append("|---|---|---|---|---|---|")
        for r in read_csv(per_miss):
            inside = "✅" if r["inside_envelope"].lower() == "true" else "❌"
            out_lines.append(
                f"| {r['mission_id']} | "
                f"{float(r['total_dv_simulated_ms']):.2f} | "
                f"{float(r['published_total_dv_ms']):.2f} | "
                f"{r['relative_error_pct']} | "
                f"{float(r['terminal_pos_err_mm']):.0f} | "
                f"{inside} |"
            )
        out_lines.append("")

    if soyuz is not None:
        import json
        with open(soyuz) as f:
            d = json.load(f)
        out_lines.append("## Soyuz MS-17 end-to-end pipeline result")
        out_lines.append("")
        out_lines.append(f"- **Phasing dv (replayed):** {d['phasing_dv_replayed_ms']:.2f} m/s")
        out_lines.append(f"- **Terminal dv (simulated):** {d['terminal_dv_simulated_ms']*1000:.1f} mm/s")
        out_lines.append(f"- **Total OOSim dv:** {d['total_dv_ms']:.3f} m/s")
        out_lines.append(f"- **Published total dv:** {d['published_total_dv_ms']:.1f} m/s")
        rel = abs(d['total_dv_ms'] - d['published_total_dv_ms']) / d['published_total_dv_ms'] * 100
        out_lines.append(f"- **Relative error:** {rel:.2f}%")
        out_lines.append(f"- **Terminal pos error:** {d['terminal_pos_error_mm']:.1f} mm")
        out_lines.append(f"- **Source DOI:** {d['primary_doi']}")
        out_lines.append("")

    out_lines.extend([
        "## Reproducibility",
        "",
        "All scripts in `experiments/scripts/` reproduce the headline numbers.",
        "Required environment: Python 3.11+, numpy, scipy, matplotlib, cvxpy, ecos, sgp4.",
        "Install via `pip install -e .[dev]` from the repo root.",
        "",
        "Bibliography in `dataset/bibliography.bib` validated via Crossref REST API.",
        "Mission data in `dataset/missions.csv` (50 missions, RPOD-50 dataset).",
        "",
        "## Cite as",
        "",
        "```bibtex",
        "@inproceedings{morais2026oosim,",
        "  author = {Morais, Giovane and Milagre da Fonseca, Ijar and Villani, Em\\'ilia},",
        "  title = {Computational Simulation of Rendezvous and Robotic Berthing for ",
        "           On-Orbit Servicing: Validation Against Operational Mission Data},",
        "  booktitle = {77th International Astronautical Congress (IAC 2026)},",
        "  address = {Antalya, T\\\"urkiye}, year = {2026}, note = {IAC-26,C2.3.6}",
        "}",
        "```",
    ])

    OUT.write_text("\n".join(out_lines))
    print(f"Wrote {OUT}")
    print(f"  Total lines: {len(out_lines)}")


if __name__ == "__main__":
    main()
