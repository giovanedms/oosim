"""Figure 1 (revised): OOSim closed-loop architecture with UKF + soft-terminal MPC.

Drawn at the exact print size of a two-column IAC figure* (\\textwidth = 486.26 pt)
so the LaTeX build includes it at scale 1.0 and every label keeps its nominal
size (7-8 pt, matching the 10 pt Times body). Coordinates are in inches.

The loop reads left to right (truth -> sensor -> UKF -> QP -> RCS) and closes
along the bottom; set-up (phasing) and the terminal capture check sit above.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIX Two Text", "STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 7.5,
    "pdf.fonttype": 42, "savefig.dpi": 600,
})

OUT = Path(__file__).resolve().parent.parent / "figures"

W, H = 486.26 / 72.27, 1.745         # figure* width in inches
ROW_Y, ROW_H = 0.40, 0.66            # closed-loop row
TOP_Y, TOP_H = 1.18, 0.54            # set-up / check row
LINE = 0.118                         # text line pitch at 7.5 pt, inches

FILL = {"truth": "#e4e4e4", "sense": "#dcebf7", "guid": "#d6efd0",
        "act": "#fbefc4", "aux": "white"}


def box(ax, x, y, w, h, title, body, kind, dashed=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
        facecolor=FILL[kind], edgecolor="black",
        linewidth=0.7, linestyle=(0, (3, 2)) if dashed else "-"))
    lines = body.split("\n") if body else []
    top = y + h / 2 + LINE * len(lines) / 2
    ax.text(x + w / 2, top, title, ha="center", va="center",
            fontsize=8, weight="bold")
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, top - LINE * (i + 1), ln, ha="center", va="center")
    return x, y, w, h


def arrow(ax, p, q, style="-|>", ls="-"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(
        arrowstyle=style, lw=0.8, color="black", linestyle=ls,
        shrinkA=0, shrinkB=0, mutation_scale=7))


def main():
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    gap, margin = 0.28, 0.03
    widths = [1.34, 1.02, 0.98, 1.30, 0.88]
    spare = W - 2 * margin - sum(widths) - gap * (len(widths) - 1)
    widths[0] += spare                     # absorb rounding into the widest label
    xs, x = [], margin
    for w in widths:
        xs.append(x); x += w + gap

    specs = [
        ("Truth propagator", "HCW relative dynamics\n6-state STM", "truth"),
        ("Sensor model", "noise 3$\\sigma$\n+ latency", "sense"),
        ("UKF", "state estimator", "sense"),
        ("QP guidance (MPC)", "receding horizon\nsoft terminal cost", "guid"),
        ("RCS actuator", "$\\Delta v$ impulse", "act"),
    ]
    boxes = [box(ax, xi, ROW_Y, w, ROW_H, t, b, k)
             for xi, w, (t, b, k) in zip(xs, widths, specs)]

    # Forward chain with the signal carried by each link.
    yc = ROW_Y + ROW_H / 2
    signals = ["$\\mathbf{x}$", "$\\mathbf{y}$", "$\\hat{\\mathbf{x}}$", "$\\Delta\\mathbf{v}$"]
    for (x0, _, w0, _), (x1, _, _, _), s in zip(boxes, boxes[1:], signals):
        arrow(ax, (x0 + w0, yc), (x1, yc))
        ax.text((x0 + w0 + x1) / 2, yc + 0.07, s, ha="center", va="bottom", fontsize=8)

    # Feedback: first impulse applied to the truth model, re-plan every step.
    xa = boxes[0][0] + boxes[0][2] / 2
    xe = boxes[-1][0] + boxes[-1][2] / 2
    yb = 0.04
    ax.plot([xe, xe, xa], [ROW_Y, yb, yb], color="black", lw=0.8)
    arrow(ax, (xa, yb), (xa, ROW_Y))
    ax.text((xa + xe) / 2, yb + 0.05,
            "first impulse applied to the truth model; re-planned at every control step",
            ha="center", va="bottom", style="italic")

    # Outside the loop: the fixed initial condition and the terminal capture check.
    # (Phasing is replayed separately; the phasing-to-terminal hand-off is not part
    # of any closed-loop result, so it is deliberately not drawn feeding the loop.)
    px, _, pw, _ = boxes[0]
    box(ax, px, TOP_Y, pw, TOP_H, "Initial state", "V-bar offset behind target", "aux", dashed=True)
    arrow(ax, (px + 0.30, TOP_Y), (px + 0.30, ROW_Y + ROW_H))

    kx = boxes[1][0]
    kw = boxes[2][0] + boxes[2][2] - kx
    box(ax, kx, TOP_Y, kw, TOP_H, "Capture-envelope check",
        "terminal position ellipsoid + speed cap", "aux", dashed=True)
    arrow(ax, (px + pw, ROW_Y + ROW_H - 0.12), (kx, TOP_Y + TOP_H / 2))

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig01_architecture_v3.{ext}")
    plt.close(fig)
    print(f"  saved {OUT / 'fig01_architecture_v3.pdf'} (+ .png)")


if __name__ == "__main__":
    main()
