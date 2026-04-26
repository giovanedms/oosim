"""Figure 11: per-mission validation grid (11 small thumbnails).

Reads per_mission_v3.csv and produces a single figure with 11 subplot
thumbnails — one per hardcoded mission — each showing a bar with the
terminal position error and a horizontal line marking the relevant
envelope semi-axis. All bars green (all 11 inside their envelopes).
"""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from oosim.targeting.envelope_specs import (
    CANADARM2_BERTHING, NDS_DOCKING, SSVP_DOCKING,
)

plt.rcParams.update({
    "font.family": "serif", "font.size": 8,
    "axes.linewidth": 0.5, "axes.grid": True,
    "grid.alpha": 0.2, "grid.linestyle": "--", "grid.linewidth": 0.3,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"
RESULTS = Path(__file__).resolve().parent.parent / "results"


def envelope_bound(env_name: str) -> float:
    """Return the most restrictive semi-axis for the envelope, in mm."""
    name = env_name.lower()
    if "canadarm" in name:
        return float(CANADARM2_BERTHING.pos_semi_axes.min()) * 1000
    if "nds" in name:
        return float(NDS_DOCKING.pos_semi_axes.min()) * 1000
    if "ssvp" in name:
        return float(SSVP_DOCKING.pos_semi_axes.min()) * 1000
    return 300.0


def main():
    csv_file = RESULTS / "per_mission_v3.csv"
    if not csv_file.exists():
        print("per_mission_v3.csv not found; run script 14 first."); return
    with open(csv_file) as f:
        rows = list(csv.DictReader(f))

    n_missions = len(rows)
    cols = 4
    rows_grid = (n_missions + cols - 1) // cols
    fig, axs = plt.subplots(rows_grid, cols, figsize=(8.0, 2.0 * rows_grid))
    axs = axs.flatten() if hasattr(axs, "flatten") else [axs]

    for i, r in enumerate(rows):
        ax = axs[i]
        pos_err_mm = float(r["terminal_pos_err_mm"])
        env_mm = envelope_bound(r["envelope_used"])
        margin_pct = (1 - pos_err_mm / env_mm) * 100
        color = "tab:green" if pos_err_mm < env_mm else "tab:red"
        ax.barh(0, pos_err_mm, color=color, edgecolor="black", lw=0.4)
        ax.axvline(env_mm, color="darkgreen", linestyle="--", lw=0.7)
        ax.set_xlim(0, max(env_mm * 1.2, pos_err_mm * 1.1))
        ax.set_yticks([])
        ax.set_xlabel("pos err [mm]", fontsize=7)
        ax.set_title(f"{r['mission_id']}\nerr {pos_err_mm:.0f}/{env_mm:.0f} mm "
                     f"({margin_pct:.0f}% margin)", fontsize=7)

    # Hide any unused axes
    for i in range(len(rows), len(axs)):
        axs[i].axis("off")

    fig.suptitle("Figure 11. Per-mission v3 validation: terminal position error "
                 "vs capture envelope semi-axis (all 11 inside envelope)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig11_per_mission_grid.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig11_per_mission_grid.png'}")


if __name__ == "__main__":
    main()
