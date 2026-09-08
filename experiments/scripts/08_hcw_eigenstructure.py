"""Figure 7: HCW state-transition matrix eigenstructure (LVLH).

Visualizes the eigenvalues of Phi(t) for a representative orbit, showing the
two oscillatory modes (cross-track + radial-along-track coupled) and the
secular along-track drift mode that is the source of the V-bar 'rolling'
behavior of natural relative motion.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from oosim.proxops.hcw import hcw_state_transition_matrix, mean_motion

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.6, "axes.grid": True,
    "grid.alpha": 0.25, "grid.linestyle": "--", "grid.linewidth": 0.4,
    "savefig.dpi": 300, "savefig.bbox": "tight",
})

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    n = mean_motion(6378.137 + 408.0)
    period = 2 * np.pi / n
    t_grid = np.linspace(0.01, period, 200)
    eigs_real = np.zeros((6, len(t_grid)))
    eigs_imag = np.zeros((6, len(t_grid)))
    for i, t in enumerate(t_grid):
        Phi = hcw_state_transition_matrix(n, t)
        eigvals = np.linalg.eigvals(Phi)
        idx = np.argsort(eigvals.imag)
        eigs_real[:, i] = eigvals[idx].real
        eigs_imag[:, i] = eigvals[idx].imag

    fig, axs = plt.subplots(1, 2, figsize=(7.5, 3.0))

    # Left: complex-plane trajectory of the 6 eigenvalues over one period
    for k in range(6):
        axs[0].plot(eigs_real[k], eigs_imag[k], lw=0.7, label=f"$\\lambda_{k+1}$")
    theta = np.linspace(0, 2 * np.pi, 200)
    axs[0].plot(np.cos(theta), np.sin(theta), "k--", lw=0.4, label="unit circle")
    axs[0].set_xlabel("Re($\\lambda$)"); axs[0].set_ylabel("Im($\\lambda$)")
    axs[0].set_title("(a) HCW STM eigenvalues over one orbit", fontsize=9)
    axs[0].set_aspect("equal")
    axs[0].set_xlim(-1.5, 1.5); axs[0].set_ylim(-1.5, 1.5)
    axs[0].legend(loc="upper right", fontsize=6, ncol=2)

    # Right: |determinant| as function of time (should be exactly 1 — symplectic)
    dets = np.array([abs(np.linalg.det(hcw_state_transition_matrix(n, t))) for t in t_grid])
    axs[1].plot(t_grid / 60, dets - 1.0, "k-", lw=0.8)
    axs[1].set_xlabel("time [min]")
    axs[1].set_ylabel("$|\\det \\Phi(t)| - 1$")
    axs[1].set_title("(b) Symplecticity check (numerical)", fontsize=9)
    axs[1].set_yscale("symlog", linthresh=1e-15)

    fig.tight_layout()
    fig.savefig(OUT / "fig07_hcw_eigenstructure.png")
    plt.close(fig)
    print(f"  saved {OUT / 'fig07_hcw_eigenstructure.png'}")


if __name__ == "__main__":
    main()
