"""Figure 8: v3 (UKF + soft-terminal MPC) Monte Carlo results.

Generates a two-panel figure summarizing the breakthrough Monte Carlo results:
  (a) success-rate heatmap across the noise/latency grid (all 100% — green)
  (b) p95 terminal pos error vs noise, colored by latency, with linear regression
"""
from pathlib import Path
import csv
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
RESULTS = Path(__file__).resolve().parent.parent / "results"


def main():
    files = sorted(RESULTS.glob("monte_carlo_soft_*.csv"))
    if not files:
        print("No v3 MC CSV found; run script 10 first."); return
    with open(files[-1]) as f:
        rows = list(csv.DictReader(f))

    noises = sorted(set(float(r["noise_3sig_m"]) for r in rows))
    lats = sorted(set(float(r["latency_s"]) for r in rows))
    success = np.zeros((len(noises), len(lats)))
    p95_pos = np.zeros((len(noises), len(lats)))
    for r in rows:
        i = noises.index(float(r["noise_3sig_m"]))
        j = lats.index(float(r["latency_s"]))
        success[i, j] = float(r["success_rate"])
        p95_pos[i, j] = float(r["pos_err_p95_m"])

    fig, axs = plt.subplots(1, 2, figsize=(7.5, 3.0))

    # Panel (a): success-rate heatmap
    im = axs[0].imshow(success * 100, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    axs[0].set_xticks(range(len(lats))); axs[0].set_xticklabels([f"{x*1000:.0f}" for x in lats])
    axs[0].set_yticks(range(len(noises))); axs[0].set_yticklabels([f"{x*1000:.0f}" for x in noises])
    axs[0].set_xlabel("communication latency [ms]")
    axs[0].set_ylabel("3$\\sigma$ position noise [mm]")
    axs[0].set_title("(a) Success rate")
    fig.colorbar(im, ax=axs[0], label="%")
    for i in range(len(noises)):
        for j in range(len(lats)):
            axs[0].text(j, i, f"{success[i,j]*100:.0f}%", ha="center", va="center",
                        fontsize=10, color="black", weight="bold")

    # Panel (b): p95 pos err vs noise, lines per latency, with linear fit
    colors = ["tab:blue", "tab:orange", "tab:red"]
    for k, lat in enumerate(lats):
        y = [p95_pos[i, k] * 1000 for i in range(len(noises))]
        x = [n * 1000 for n in noises]
        axs[1].plot(x, y, "o-", color=colors[k], lw=1.0, markersize=5,
                    label=f"{lat*1000:.0f} ms latency")
    # Reference: CANADARM2 envelope semi-axis (300 mm worst case)
    axs[1].axhline(300, color="green", linestyle="--", lw=0.8, alpha=0.7,
                    label="CANADARM2 envelope (300 mm)")
    axs[1].set_xlabel("3$\\sigma$ position noise [mm]")
    axs[1].set_ylabel("p95 terminal position error [mm]")
    axs[1].set_xscale("log"); axs[1].set_yscale("log")
    axs[1].set_title("(b) Error scaling vs noise")
    axs[1].legend(loc="upper left", fontsize=7)

    fig.tight_layout()
    fig.savefig(OUT / "fig08_v3_results.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig08_v3_results.png'}")


if __name__ == "__main__":
    main()
