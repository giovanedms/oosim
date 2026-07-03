"""Figure 1 (revised): OOSim architecture with UKF + soft-terminal MPC.

Updates the v0 architecture diagram (script 02) to reflect the v3 pipeline:
the UKF is shown explicitly as the upstream filter feeding the QP, and the
soft-terminal-cost is annotated.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.6, "savefig.dpi": 300, "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"


def main():
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")

    # Top row: open-loop modules (simulator components)
    boxes_top = [
        (0.3, 5.3, 2.0, 1.0, "phasing\n(Hohmann + J2 +\nfinite burn)", "lightblue"),
        (3.0, 5.3, 2.0, 1.0, "proxops\n(HCW STM 6×6 +\nV-bar corridor)", "lightblue"),
        (5.7, 5.3, 2.0, 1.0, "attitude\n(quaternion +\nRCS phase-plane)", "lightblue"),
    ]
    # Center row: closed-loop control pipeline (the v3 contribution)
    boxes_mid = [
        (0.3, 3.0, 1.8, 1.4, "sensor\n(LIDAR/camera)\n+ noise +\nlatency", "lightyellow"),
        (2.5, 3.0, 1.8, 1.4, "UKF\n(state estimator)\n[NEW in v3]", "lightgreen"),
        (4.7, 3.0, 2.4, 1.4, "QP solver\n(soft terminal cost,\n$\\lambda_T = 1000$)\n[v3 reformulation]", "lightgreen"),
        (7.4, 3.0, 1.8, 1.4, "RCS\nactuator\n(Δv impulse)", "lightyellow"),
    ]
    # Bottom: target + envelope
    boxes_bot = [
        (3.0, 0.6, 5.0, 1.4, "target spacecraft + capture envelope\n(workspace ellipsoid + attitude alignment + rate caps)", "lightcoral"),
    ]

    for x, y, w, h, label, color in boxes_top + boxes_mid + boxes_bot:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                     facecolor=color, edgecolor="black", linewidth=0.8))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=8)

    # Vertical labels for layers
    ax.text(0.05, 5.8, "Simulator\nlayer", ha="left", va="center", fontsize=8,
            style="italic", color="navy", rotation=0)
    ax.text(0.05, 3.7, "Closed-loop\ncontrol", ha="left", va="center", fontsize=8,
            style="italic", color="darkgreen", rotation=0)

    # Arrows: simulator -> sensor
    arrows = [
        ((1.3, 5.3), (1.2, 4.4)),  # phasing -> sensor
        ((4.0, 5.3), (3.4, 4.4)),  # proxops -> UKF
        ((6.7, 5.3), (5.9, 4.4)),  # attitude -> QP
        # Closed-loop chain
        ((2.1, 3.7), (2.5, 3.7)),  # sensor -> UKF
        ((4.3, 3.7), (4.7, 3.7)),  # UKF -> QP
        ((7.1, 3.7), (7.4, 3.7)),  # QP -> actuator
        # Actuator -> target
        ((8.3, 3.0), (6.0, 2.0)),  # actuator -> target
        # Target -> sensor (feedback)
        ((4.5, 1.3), (1.5, 3.0)),
    ]
    for src, dst in arrows:
        ax.annotate("", xy=dst, xytext=src,
                    arrowprops=dict(arrowstyle="->", lw=0.7, color="black"))

    ax.text(5.5, 6.8, "OOSim v3 architecture (validated 14/14 missions, 100/100 trials at central cell)",
            ha="center", fontsize=10, weight="bold")
    fig.savefig(OUT / "fig01_architecture_v3.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig01_architecture_v3.png'}")


if __name__ == "__main__":
    main()
