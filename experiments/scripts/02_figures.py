"""Generate Section 5 figures for the IAC paper.

Outputs PNG files into experiments/figures/.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from oosim.proxops.hcw import mean_motion
from oosim.proxops.vbar import vbar_corridor_bounds
from oosim.targeting.envelope_specs import CANADARM2_BERTHING, NDS_DOCKING, SSVP_DOCKING
from oosim.targeting.qp_targeting import qp_terminal_target


# ---------- Style: AIAA-like, monochrome-friendly ----------
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.linewidth": 0.6,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
    "grid.linewidth": 0.4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def fig_architecture():
    """Figure 1: OOSim modular architecture (block diagram)."""
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")

    boxes = [
        (0.5, 4.5, 2.0, 1.0, "phasing\n(Hohmann + J2 +\nfinite burn)"),
        (3.5, 4.5, 2.0, 1.0, "proxops\n(HCW STM 6×6 +\nV-bar corridor)"),
        (6.5, 4.5, 2.0, 1.0, "attitude\n(quaternion +\nRCS phase-plane)"),
        (2.0, 2.5, 2.0, 1.0, "targeting\n(capture envelope\n+ QP solver)"),
        (5.0, 2.5, 2.0, 1.0, "validation\n(RPOD-50 loader\n+ metrics)"),
        (3.5, 0.5, 3.0, 1.0, "experiments\n(scripts, notebooks, figures)"),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                     facecolor="white", edgecolor="black", linewidth=0.8))
        ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=8)

    # Data-flow arrows
    arrows = [
        ((2.5, 5.0), (3.5, 5.0)),  # phasing -> proxops
        ((5.5, 5.0), (6.5, 5.0)),  # proxops -> attitude
        ((4.5, 4.5), (3.5, 3.5)),  # proxops -> targeting
        ((7.0, 4.5), (4.0, 3.5)),  # attitude -> targeting
        ((3.0, 2.5), (4.0, 1.5)),  # targeting -> experiments
        ((5.5, 2.5), (5.0, 1.5)),  # validation -> experiments
    ]
    for src, dst in arrows:
        ax.annotate("", xy=dst, xytext=src,
                    arrowprops=dict(arrowstyle="->", lw=0.7, color="black"))

    fig.savefig(OUT / "fig01_architecture.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig01_architecture.png'}")


def fig_vbar_corridor():
    """Figure 2: V-bar corridor with three approach trajectories."""
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 3.0))

    # Top-down view: along-track (x_axis) vs lateral (y_axis_lvlh = LVLH y / V-bar perpendicular)
    x_at = np.linspace(0, 200, 400)  # along-track distance to target [m]
    yb, _ = zip(*[vbar_corridor_bounds(xi) for xi in x_at])
    yb = np.array(yb)

    for ax, label, ylab in [(axs[0], "Lateral / radial deviation [m]", "x_LVLH (R-bar) [m]"),
                              (axs[1], "Cross-track deviation [m]", "z_LVLH [m]")]:
        ax.fill_between(x_at, -yb, yb, color="lightgray", alpha=0.6,
                        label="V-bar corridor")
        ax.plot([0, 200], [0, 0], "k-", lw=0.5)
        ax.set_xlabel("along-track distance to target [m]")
        ax.set_ylabel(label)
        ax.set_xlim(0, 200); ax.set_ylim(-30, 30)
        ax.invert_xaxis()
        ax.legend(loc="upper right", fontsize=8)

    # Synthetic trajectories on the lateral plot
    n = mean_motion(6378.137 + 408.0)
    for init_state, color, lab in [
        (np.array([3., -200., 0., 0., 0., 0.]), "tab:blue", "34-orbit profile"),
        (np.array([5., -200., 1., 0., 0., 0.]), "tab:orange", "4-orbit profile"),
        (np.array([2., -200., -1., 0., 0., 0.]), "tab:green", "2-orbit profile"),
    ]:
        result = qp_terminal_target(
            initial_state=init_state, target_pos=np.array([0., 0., 0.]),
            n=n, horizon_steps=20, dt=15.0,
            capture_radius=0.5, v_max_terminal=0.05, dv_max_per_step=0.3,
            enforce_vbar_corridor=True,
        )
        if result.success:
            axs[0].plot(-result.states[:, 1], result.states[:, 0], color=color,
                        lw=1.0, label=lab)
            axs[1].plot(-result.states[:, 1], result.states[:, 2], color=color, lw=1.0)
    axs[0].legend(loc="upper right", fontsize=7)

    fig.tight_layout()
    fig.savefig(OUT / "fig02_vbar_corridor.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig02_vbar_corridor.png'}")


def fig_capture_envelope():
    """Figure 3: Capture envelope visualization for the 3 documented presets."""
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    fig = plt.figure(figsize=(8.0, 3.0))
    presets = [(CANADARM2_BERTHING, "Canadarm2 berthing\n(Cygnus / HTV)"),
               (NDS_DOCKING, "NDS / IDSS soft-capture\n(Crew Dragon, Starliner)"),
               (SSVP_DOCKING, "SSVP-G4000 docking\n(Soyuz / Progress)")]
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 15)
    for i, (env, title) in enumerate(presets, 1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        sx, sy, sz = env.pos_semi_axes
        x = sx * np.outer(np.cos(u), np.sin(v))
        y = sy * np.outer(np.sin(u), np.sin(v))
        z = sz * np.outer(np.ones_like(u), np.cos(v))
        ax.plot_surface(x, y, z, color="tab:blue", alpha=0.25, edgecolor="k", linewidth=0.2)
        ax.set_title(title + f"\nsemi-axes {env.pos_semi_axes.tolist()} m,\n"
                     f"||v||≤{env.vel_max} m/s, ±{np.rad2deg(env.att_tolerance_rad):.0f}°",
                     fontsize=7)
        ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
        ax.set_box_aspect([1, 1, 1])

    fig.tight_layout()
    fig.savefig(OUT / "fig03_capture_envelopes.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig03_capture_envelopes.png'}")


def fig_gain_scheduling():
    """Figure 4: gain-scheduling profile across mission phases."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    phases = ["Launch +\nascent", "Orbital\nphasing", "Far-field\napproach",
              "Mid-field\napproach", "Terminal\ncapture"]
    bandwidth = [5.0, 0.5, 0.2, 0.1, 0.05]  # rad/s, illustrative
    x = np.arange(len(phases))
    ax.bar(x, bandwidth, width=0.55, color="tab:gray", edgecolor="black", linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(phases, fontsize=8)
    ax.set_ylabel("attitude-loop bandwidth [rad/s]")
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(OUT / "fig04_gain_scheduling.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig04_gain_scheduling.png'}")


def main():
    print("Generating figures into", OUT)
    fig_architecture()
    fig_vbar_corridor()
    fig_capture_envelope()
    fig_gain_scheduling()
    print("Done.")


if __name__ == "__main__":
    main()
