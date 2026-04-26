"""Figure 9: visual cascade of v0/v1/v2/v3 results.

Bar chart comparing success rate and p95 terminal pos error for the four
versions of the Monte Carlo, at the central cell (5 cm noise, 100 ms latency).
This is the "headline" figure of Section 5 — visualizes the architectural
journey from cosmetic-success (v0) to genuine-success (v3).
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.6, "axes.grid": True,
    "grid.alpha": 0.25, "grid.linestyle": "--", "grid.linewidth": 0.4,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"


def main():
    versions = ["v0\nopen-loop\n(cosmetic)",
                "v1\nMPC hard\n(no UKF)",
                "v2\nUKF + hard",
                "v3\nUKF + soft\n+ gentler"]
    success_pct = [100, 0, 0, 100]
    # p95 pos error in mm at central cell (5cm noise, 100ms latency)
    p95_err = [0.4, 1080, 1027, 53]
    # Mean total dv mm/s
    mean_dv = [0.94, 386, 388, 486]

    fig, axs = plt.subplots(1, 3, figsize=(9.0, 3.0))
    colors = ["lightgray", "#d62728", "#d62728", "#2ca02c"]

    # Panel (a): success rate
    bars = axs[0].bar(range(4), success_pct, color=colors, edgecolor="black", lw=0.6)
    axs[0].set_xticks(range(4))
    axs[0].set_xticklabels(versions, fontsize=7)
    axs[0].set_ylabel("Success rate [%]")
    axs[0].set_ylim(0, 120)
    axs[0].set_title("(a) Success rate at central cell")
    for b, v in zip(bars, success_pct):
        axs[0].text(b.get_x() + b.get_width()/2, v + 3, f"{v}%",
                    ha="center", va="bottom", fontsize=9, weight="bold")

    # Panel (b): p95 pos error (log scale)
    bars = axs[1].bar(range(4), p95_err, color=colors, edgecolor="black", lw=0.6)
    axs[1].set_xticks(range(4))
    axs[1].set_xticklabels(versions, fontsize=7)
    axs[1].set_ylabel("p95 terminal pos error [mm]")
    axs[1].set_yscale("log")
    axs[1].set_ylim(0.1, 5000)
    axs[1].axhline(300, color="green", linestyle="--", lw=0.8, alpha=0.7,
                   label="CANADARM2 envelope (300 mm)")
    axs[1].set_title("(b) Terminal position error")
    axs[1].legend(loc="upper right", fontsize=7)
    for b, v in zip(bars, p95_err):
        axs[1].text(b.get_x() + b.get_width()/2, v * 1.4, f"{v} mm",
                    ha="center", va="bottom", fontsize=8)

    # Panel (c): mean total dv (log scale)
    bars = axs[2].bar(range(4), mean_dv, color=colors, edgecolor="black", lw=0.6)
    axs[2].set_xticks(range(4))
    axs[2].set_xticklabels(versions, fontsize=7)
    axs[2].set_ylabel("Mean terminal $\\Delta v$ [mm/s]")
    axs[2].set_yscale("log")
    axs[2].set_ylim(0.5, 2000)
    axs[2].set_title("(c) Propellant cost")
    for b, v in zip(bars, mean_dv):
        axs[2].text(b.get_x() + b.get_width()/2, v * 1.4, f"{v}",
                    ha="center", va="bottom", fontsize=8)

    fig.suptitle("Figure 9. v0 → v3 architectural cascade at the central noise/latency cell\n"
                 "(5 cm 3-$\\sigma$ position noise, 100 ms communication latency)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig09_cascade.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig09_cascade.png'}")


if __name__ == "__main__":
    main()
