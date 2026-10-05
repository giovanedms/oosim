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

# Drawn at the exact two-column print width (\textwidth = 486.26 pt) and included
# at scale 1.0, so every label prints at its nominal 7-8 pt size.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIX Two Text", "STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "axes.grid": True,
    "grid.alpha": 0.25, "grid.linestyle": "--", "grid.linewidth": 0.4,
    "pdf.fonttype": 42, "savefig.dpi": 600,
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

    fig, (axh, axc) = plt.subplots(1, 2, figsize=(486.26 / 72.27, 2.45),
                                   layout="constrained",
                                   gridspec_kw={"width_ratios": [1.12, 1.0]})

    # Panel (a): heatmap, coloured and annotated in the same unit (percent).
    cmap = plt.get_cmap("RdYlGn")
    # Full 0-100 scale: a clipped 80-100 range painted 72% and 0% the same red.
    norm = matplotlib.colors.Normalize(vmin=0, vmax=100)
    pct = grid * 100
    im = axh.imshow(pct, aspect="auto", cmap=cmap, norm=norm, origin="lower")
    axh.grid(False)
    axh.set_xticks(range(len(lats)))
    axh.set_xticklabels([f"{int(lat*1000)}" for lat in lats])
    axh.set_yticks(range(len(noises)))
    axh.set_yticklabels([f"{int(n*1000)}" for n in noises])
    axh.set_xlabel("Estimator / actuation latency (ms)")
    axh.set_ylabel(r"Sensor noise 3$\sigma$ (mm)")
    axh.set_title("(a) Capture success (%); box: realistic sensors")
    for i in range(len(noises)):
        for j in range(len(lats)):
            r, g, b, _ = cmap(norm(pct[i, j]))
            dark = 0.299 * r + 0.587 * g + 0.114 * b < 0.5
            axh.text(j, i, f"{pct[i, j]:.0f}" if pct[i, j] >= 99.95 else f"{pct[i, j]:.1f}",
                     ha="center", va="center", fontsize=7,
                     color="white" if dark else "black")
    # Box the plausible-sensor band (legend lives in the panel title).
    plausible_rows = [i for i, n in enumerate(noises) if n <= PLAUSIBLE_NOISE_MAX]
    if plausible_rows:
        axh.add_patch(plt.Rectangle(
            (-0.5, -0.5), len(lats), max(plausible_rows) + 1,
            fill=False, edgecolor="navy", linewidth=1.6, linestyle="-"))
    cb = fig.colorbar(im, ax=axh, fraction=0.05, pad=0.02,
                      ticks=[0, 20, 40, 60, 80, 100])
    cb.set_label("success (%)", fontsize=7)
    cb.ax.tick_params(labelsize=6.5)

    # Panel (b): success vs noise, one curve per latency. Curves are labelled
    # at their right-hand end: a legend box inevitably covers one of the drops.
    x_mm = [n * 1000 for n in noises]
    x_end = x_mm[-1]
    for j, lat in enumerate(lats):
        line, = axc.plot(x_mm, pct[:, j], marker="o", markersize=3, linewidth=1.0)
        axc.text(x_end + 45, pct[-1, j], f"{int(lat*1000)} ms", color=line.get_color(),
                 ha="left", va="center", fontsize=7)
    axc.text(x_end + 45, max(pct[-1, :]) + 13, "latency", ha="left", va="center",
             fontsize=7, style="italic")
    axc.axvspan(0, PLAUSIBLE_NOISE_MAX * 1000, color="0.85", alpha=0.7)
    axc.text(PLAUSIBLE_NOISE_MAX * 500, 45, "realistic sensors", rotation=90,
             ha="center", va="center", fontsize=6.5, color="0.3")
    axc.set_xlabel(r"Sensor noise 3$\sigma$ (mm)")
    axc.set_ylabel("Capture success (%)")
    axc.set_title("(b) Success versus sensor noise")
    axc.set_xlim(0, x_end + 330)
    axc.set_xticks([0, 200, 400, 600, 800, 1000, 1200, 1400])
    axc.set_ylim(-3, 103)

    out_png = OUT / "fig12_failure_boundary.png"
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig12_failure_boundary.{ext}")
    print(f"Saved {OUT / 'fig12_failure_boundary.pdf'} (+ {out_png.name})")

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
