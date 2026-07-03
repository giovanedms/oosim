"""Generate Section 5 validation comparison bar chart figure.

Compares simulated total Δv against published values for the missions where
both are available, reading the real v3 pipeline results from
experiments/results/per_mission_v3.csv (script 14). Saves PNG to
experiments/figures/.
"""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.6, "axes.grid": True,
    "grid.alpha": 0.25, "grid.linestyle": "--", "grid.linewidth": 0.4,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def fig_validation_comparison():
    """Bar chart: per-mission published vs simulated total Δv (where available).

    Reads the actual v3 closed-loop results (per_mission_v3.csv, script 14) and
    plots published vs simulated totals for the missions with a documented
    published Δv (Soyuz MS-17, Apollo 11 LM RDV, ASTP), annotating the relative
    error. Log scale because Apollo (~1770 m/s) dwarfs ASTP (~28 m/s).
    """
    results_dir = Path(__file__).resolve().parent.parent / "results"
    csv_file = results_dir / "per_mission_v3.csv"
    if not csv_file.exists():
        print("  per_mission_v3.csv not found; run script 14 first")
        return
    with open(csv_file) as f:
        rows = [r for r in csv.DictReader(f)
                if float(r["published_total_dv_ms"]) > 0]
    names = [r["mission_id"] for r in rows]
    published = np.array([float(r["published_total_dv_ms"]) for r in rows])
    simulated = np.array([float(r["total_dv_simulated_ms"]) for r in rows])
    rel_err = [r["relative_error_pct"] for r in rows]

    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    x = np.arange(len(names))
    w = 0.35
    ax.bar(x - w / 2, published, w, label="published", color="tab:gray", edgecolor="black", lw=0.6)
    ax.bar(x + w / 2, simulated, w, label="OOSim simulated (v3)", color="tab:blue", edgecolor="black", lw=0.6)
    ax.set_yscale("log")
    ax.set_ylim(top=float(published.max()) * 8)
    for xi, pub, sim, err in zip(x, published, simulated, rel_err):
        ax.text(xi, max(pub, sim) * 1.3,
                f"pub {pub:.2f}\nsim {sim:.2f}\nerr {err}%",
                ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=7)
    ax.set_ylabel("total $\\Delta v$ [m/s] (log)")
    ax.set_title("Figure 5. Total $\\Delta v$ comparison: published vs OOSim v3", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig05_validation_comparison.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig05_validation_comparison.png'}")
    for nm, pub, sim, err in zip(names, published, simulated, rel_err):
        print(f"    {nm:20} published={pub:8.2f}  simulated={sim:8.2f}  rel_err={err}%")


def fig_mc_heatmap():
    """Heatmap of MC results: success rate by (noise, latency) cell.

    Reads the most recent monte_carlo_mpc_*.csv file from results/ if it exists,
    otherwise falls back to monte_carlo_noise_*.csv.
    """
    results_dir = Path(__file__).resolve().parent.parent / "results"
    files = sorted(results_dir.glob("monte_carlo_mpc_*.csv")) or \
             sorted(results_dir.glob("monte_carlo_noise_*.csv"))
    if not files:
        print("  no MC results CSV found; skipping heatmap")
        return
    import csv
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

    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.8))
    im0 = axs[0].imshow(success, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    axs[0].set_xticks(range(len(lats)))
    axs[0].set_xticklabels([f"{x*1000:.0f}" for x in lats])
    axs[0].set_yticks(range(len(noises)))
    axs[0].set_yticklabels([f"{x*1000:.0f}" for x in noises])
    axs[0].set_xlabel("communication latency [ms]")
    axs[0].set_ylabel("3$\\sigma$ position noise [mm]")
    axs[0].set_title("(a) success rate")
    fig.colorbar(im0, ax=axs[0])
    for i in range(len(noises)):
        for j in range(len(lats)):
            axs[0].text(j, i, f"{success[i,j]:.0%}", ha="center", va="center",
                        fontsize=8, color="black")

    im1 = axs[1].imshow(p95_pos * 1000, cmap="viridis", aspect="auto")
    axs[1].set_xticks(range(len(lats)))
    axs[1].set_xticklabels([f"{x*1000:.0f}" for x in lats])
    axs[1].set_yticks(range(len(noises)))
    axs[1].set_yticklabels([f"{x*1000:.0f}" for x in noises])
    axs[1].set_xlabel("communication latency [ms]")
    axs[1].set_ylabel("3$\\sigma$ position noise [mm]")
    axs[1].set_title("(b) p95 terminal pos error [mm]")
    fig.colorbar(im1, ax=axs[1])
    for i in range(len(noises)):
        for j in range(len(lats)):
            axs[1].text(j, i, f"{p95_pos[i,j]*1000:.1f}", ha="center", va="center",
                        fontsize=8, color="white")

    fig.suptitle("Figure 6. Monte Carlo robustness across noise/latency grid", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig06_mc_heatmap.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig06_mc_heatmap.png'}")


def main():
    fig_validation_comparison()
    fig_mc_heatmap()
    print("Done.")


if __name__ == "__main__":
    main()
