"""Figure 9: visual cascade of v0/v1/v2/v3 results.

Bar chart comparing success rate and p95 terminal pos error for the four
versions of the Monte Carlo, at the central cell (5 cm noise, 100 ms latency).
This is the "headline" figure of Section 5 — visualizes the architectural
journey from cosmetic-success (v0) to genuine-success (v3).

Values are read from the latest Monte Carlo CSVs in experiments/results/
(monte_carlo_noise = v0, monte_carlo_mpc = v1, monte_carlo_ukf = v2,
monte_carlo_soft = v3), central cell noise_3sig_m=0.05, latency_s=0.10.
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

# Drawn at the exact single-column print width (\columnwidth = 231.75 pt) and
# included at scale 1.0, so every label prints at its nominal 6.5-8 pt size.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIX Two Text", "STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 7, "axes.titlesize": 7.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 6.5,
    "axes.linewidth": 0.6, "axes.grid": True, "axes.axisbelow": True,
    "grid.alpha": 0.25, "grid.linestyle": "--", "grid.linewidth": 0.4,
    "pdf.fonttype": 42, "savefig.dpi": 600,
})

OUT = Path(__file__).resolve().parent.parent / "figures"
RESULTS = Path(__file__).resolve().parent.parent / "results"

CENTRAL_NOISE = 0.05   # 5 cm 3-sigma
CENTRAL_LATENCY = 0.10  # 100 ms


def central_cell(pattern: str) -> dict:
    """Read the central noise/latency cell from the latest CSV matching pattern."""
    files = sorted(RESULTS.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no results CSV matching {pattern} in {RESULTS}")
    with open(files[-1]) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if (abs(float(r["noise_3sig_m"]) - CENTRAL_NOISE) < 1e-9
                and abs(float(r["latency_s"]) - CENTRAL_LATENCY) < 1e-9):
            return r
    raise ValueError(f"central cell not found in {files[-1]}")


def main():
    versions = ["v0\nopen-loop\n(cosmetic)",
                "v1\nMPC hard\n(no UKF)",
                "v2\nUKF + hard",
                "v3\nUKF + soft\n+ gentler"]
    cells = [central_cell(p) for p in ("monte_carlo_noise_*.csv",
                                       "monte_carlo_mpc_*.csv",
                                       "monte_carlo_ukf_*.csv",
                                       "monte_carlo_soft_*.csv")]
    success_pct = [round(float(c["success_rate"]) * 100) for c in cells]
    # p95 pos error in mm at central cell (5cm noise, 100ms latency)
    p95_err = [float(c["pos_err_p95_m"]) * 1000 for c in cells]
    # Mean total dv mm/s
    mean_dv = [float(c["total_dv_mean_ms"]) * 1000 for c in cells]
    for v, s, p, d in zip(versions, success_pct, p95_err, mean_dv):
        print(f"  {v.splitlines()[0]:4} success={s}%  p95={p:.1f} mm  mean_dv={d:.1f} mm/s")

    # Tick labels carry only the version tag; the caption spells out each
    # generation, which the full "v0\nopen-loop\n(cosmetic)" labels could not
    # do legibly at column width.
    tags = [v.splitlines()[0] for v in versions]
    fig, axs = plt.subplots(1, 3, figsize=(231.75 / 72.27, 1.75), layout="constrained")
    colors = ["lightgray", "#d62728", "#d62728", "#2ca02c"]

    def bars_with_labels(ax, values, labels, title, log, ylim, offset):
        bars = ax.bar(range(4), values, width=0.72, color=colors,
                      edgecolor="black", lw=0.5)
        ax.set_xticks(range(4))
        ax.set_xticklabels(tags)
        ax.tick_params(axis="both", length=2, pad=1.5)
        if log:
            ax.set_yscale("log")
        ax.set_ylim(*ylim)
        ax.set_title(title, pad=3)
        for b, v, lab in zip(bars, values, labels):
            y = v * offset if log else v + offset
            ax.text(b.get_x() + b.get_width() / 2, y, lab,
                    ha="center", va="bottom", fontsize=6.5)
        if log:
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        return bars

    # Panel (a): success rate
    bars_with_labels(axs[0], success_pct, [f"{v}" for v in success_pct],
                     "(a) Success (%)", log=False, ylim=(0, 118), offset=2)

    # Panel (b): p95 pos error (log scale)
    # Neutral colour: green is already the v3 bar.
    axs[1].axhline(300, color="0.25", linestyle="--", lw=0.8, zorder=0.5)
    axs[1].text(3.45, 300 * 1.2, "300", ha="right", va="bottom", fontsize=6.5, color="0.25")
    bars_with_labels(axs[1], p95_err,
                     [f"{v:.1f}" if v < 10 else f"{v:.0f}" for v in p95_err],
                     "(b) p95 error (mm)", log=True, ylim=(0.1, 5000), offset=1.25)

    # Panel (c): mean total dv (log scale)
    # Linear axis: on a log axis the 434 -> 516 mm/s step (the propellant price of
    # the soft formulation discussed in Section 5.4) was visually flat.
    bars_with_labels(axs[2], mean_dv, [f"{v:.0f}" for v in mean_dv],
                     "(c) Mean $\\Delta v$ (mm/s)", log=False, ylim=(0, 640), offset=8)

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig09_cascade.{ext}")
    plt.close(fig)
    print(f"  saved {OUT / 'fig09_cascade.pdf'} (+ .png)")


if __name__ == "__main__":
    main()
