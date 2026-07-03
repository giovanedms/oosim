"""Figure 12: v3 failure-boundary map beyond the plausible sensor envelope.

Consumes the newest experiments/results/failure_boundary_*.csv (script 25) and
renders two panels:
  (a) capture-success-rate heatmap over the noise x latency grid, annotated with
      the per-cell rate; the plausible-sensor band (<=200 mm 3-sigma) is boxed.
  (b) success rate vs 3-sigma sensor noise, one curve per latency, with the
      realistic-sensor region shaded to show that degradation only begins far
      outside any operational rendezvous sensor.

Output: experiments/figures/fig12_failure_boundary.png
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
# Upper bound of a realistic relative-navigation sensor 3-sigma error (m).
PLAUSIBLE_NOISE_MAX = 0.20


def main():
    files = sorted(RESULTS.glob("failure_boundary_*.csv"))
    if not files:
        print("No failure_boundary CSV found; run script 25 first.")
        return
    with open(files[-1]) as f:
        rows = list(csv.DictReader(f))

    noises = sorted({float(r["noise_3sig_m"]) for r in rows})
    lats = sorted({float(r["latency_s"]) for r in rows})
    grid = np.full((len(noises), len(lats)), np.nan)
    for r in rows:
        i = noises.index(float(r["noise_3sig_m"]))
        j = lats.index(float(r["latency_s"]))
        grid[i, j] = float(r["success_rate"])

    fig, (axh, axc) = plt.subplots(1, 2, figsize=(9.2, 4.0))

    # Panel (a): heatmap
    im = axh.imshow(grid, aspect="auto", cmap="RdYlGn", vmin=0.8, vmax=1.0,
                    origin="lower")
    axh.set_xticks(range(len(lats)))
    axh.set_xticklabels([f"{int(lat*1000)}" for lat in lats])
    axh.set_yticks(range(len(noises)))
    axh.set_yticklabels([f"{int(n*1000)}" for n in noises])
    axh.set_xlabel("Estimator / actuation latency (ms)")
    axh.set_ylabel(r"Sensor noise 3$\sigma$ (mm)")
    axh.set_title("(a) Capture-success rate")
    for i in range(len(noises)):
        for j in range(len(lats)):
            axh.text(j, i, f"{grid[i, j]*100:.1f}", ha="center", va="center",
                     fontsize=7, color="black")
    # Box the plausible-sensor band.
    plausible_rows = [i for i, n in enumerate(noises) if n <= PLAUSIBLE_NOISE_MAX]
    if plausible_rows:
        axh.add_patch(plt.Rectangle(
            (-0.5, -0.5), len(lats), max(plausible_rows) + 1,
            fill=False, edgecolor="navy", linewidth=1.6, linestyle="-"))
        axh.text(len(lats) - 0.5, max(plausible_rows), " realistic\n sensors",
                 fontsize=7, color="navy", va="top", ha="right")
    fig.colorbar(im, ax=axh, fraction=0.046, pad=0.04, label="success rate")

    # Panel (b): success vs noise, one curve per latency
    for j, lat in enumerate(lats):
        axc.plot([n * 1000 for n in noises], grid[:, j] * 100,
                 marker="o", markersize=3.5, linewidth=1.1,
                 label=f"{int(lat*1000)} ms")
    axc.axvspan(0, PLAUSIBLE_NOISE_MAX * 1000, color="0.85", alpha=0.6,
                label="realistic band")
    axc.set_xlabel(r"Sensor noise 3$\sigma$ (mm)")
    axc.set_ylabel("Capture-success rate (%)")
    axc.set_title("(b) Degradation with sensor noise")
    axc.set_ylim(75, 101)
    axc.legend(fontsize=7, title="latency", ncol=2)

    fig.tight_layout()
    out_png = OUT / "fig12_failure_boundary.png"
    fig.savefig(out_png)
    print(f"Saved {out_png}")

    # Console summary of the boundary.
    full = [n for n in noises
            if all(grid[noises.index(n), j] >= 1.0 for j in range(len(lats)))]
    print(f"Highest noise 3sigma holding 100% at every latency: "
          f"{max(full)*1000:.0f} mm" if full else "No fully-100% noise row")
    worst = min(rows, key=lambda r: float(r["success_rate"]))
    print(f"Worst cell: {float(worst['noise_3sig_m'])*1000:.0f} mm / "
          f"{float(worst['latency_s'])*1000:.0f} ms -> "
          f"{float(worst['success_rate'])*100:.1f}%")


if __name__ == "__main__":
    main()
