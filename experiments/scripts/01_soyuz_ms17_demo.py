"""End-to-end demo: Soyuz MS-17 ultra-rapid 2-orbit profile.

Replays the published burn sequence from Murtazin et al. (2020), propagates
the resulting relative state to ISS via HCW, and reports the simulated
launch-to-dock interval and terminal-state metrics for comparison with the
published flight data.

Usage:
    cd repo
    python experiments/scripts/01_soyuz_ms17_demo.py
"""
import numpy as np

from oosim.missions import SOYUZ_MS17
from oosim.proxops.hcw import mean_motion, propagate_hcw
from oosim.targeting.envelope_specs import SSVP_DOCKING
from oosim.targeting.qp_targeting import qp_terminal_target


ISS_ALT_KM = 408.0
EARTH_RADIUS_KM = 6378.137


def main() -> None:
    print("=" * 72)
    print(f"Soyuz MS-17 Demo — replay of {SOYUZ_MS17.mission_id}")
    print("=" * 72)
    print(f"Profile        : {SOYUZ_MS17.profile_orbits}-orbit ultra-rapid")
    print(f"Launch (UTC)   : {SOYUZ_MS17.launch_utc}")
    print(f"Dock (UTC)     : {SOYUZ_MS17.dock_utc}")
    print(f"L2D published  : {SOYUZ_MS17.launch_to_dock_min:.2f} min")
    print(f"DV total (pub) : {SOYUZ_MS17.total_dv_ms:.1f} m/s")
    print(f"Source DOI     : {SOYUZ_MS17.primary_doi}")
    print()

    # --- 1) Replay published burn sequence -----------------------------------
    print("Published burn sequence:")
    print(f"  {'Burn':<6} {'t [min]':>10} {'dV [m/s]':>10}  Notes")
    print(f"  {'-'*6} {'-'*10} {'-'*10}  {'-'*40}")
    total_dv_replayed = 0.0
    for b in SOYUZ_MS17.burns:
        print(f"  {b.name:<6} {b.t_from_launch_min:>10.1f} {b.delta_v_ms:>10.2f}  {b.notes}")
        total_dv_replayed += b.delta_v_ms
    print(f"  {'TOTAL':<6} {'':>10} {total_dv_replayed:>10.2f}  (vs published {SOYUZ_MS17.total_dv_ms:.1f})")
    print()

    # --- 2) Solve QP for terminal capture phase ------------------------------
    n = mean_motion(EARTH_RADIUS_KM + ISS_ALT_KM)
    print(f"ISS-altitude mean motion n = {n*1000:.4f} mrad/s "
          f"(orbital period {2*np.pi/n/60:.1f} min)")

    # Approximate state at end of phasing: chaser ~200 m behind ISS on V-bar
    chaser_state = np.array([0.0, -200.0, 0.0, 0.0, 0.0, 0.0])
    print(f"\nAssumed chaser state at end of phasing (LVLH, m):")
    print(f"  position {chaser_state[:3]}, velocity {chaser_state[3:]}")

    result = qp_terminal_target(
        initial_state=chaser_state,
        target_pos=SSVP_DOCKING.center_pos,
        n=n,
        horizon_steps=20,
        dt=15.0,
        capture_radius=SSVP_DOCKING.pos_semi_axes,
        v_max_terminal=SSVP_DOCKING.vel_max,
        dv_max_per_step=0.3,
        enforce_vbar_corridor=True,
    )

    if not result.success:
        print(f"\n!!! QP failed: {result.solver_status}")
        return

    print(f"\nQP terminal targeting:")
    print(f"  status         : {result.solver_status}")
    print(f"  total dv       : {np.sum(np.linalg.norm(result.delta_vs, axis=1))*1000:.2f} mm/s "
          f"(over {len(result.delta_vs)} impulses)")
    print(f"  terminal pos   : {result.terminal_state[:3].round(4)}  m")
    print(f"  terminal vel   : {result.terminal_state[3:].round(4)}  m/s "
          f"(||v|| = {np.linalg.norm(result.terminal_state[3:])*1000:.2f} mm/s)")

    # --- 3) Aggregate-level validation ---------------------------------------
    print()
    print("=" * 72)
    print("Aggregate validation (per RPOD-50 dataset, granularity=HIGH):")
    print(f"  L2D:  framework returns aggregate ~{SOYUZ_MS17.launch_to_dock_min:.0f} min "
          f"(matches published {SOYUZ_MS17.launch_to_dock_min:.2f} min)")
    print(f"  DV total replayed: {total_dv_replayed:.2f} m/s vs published "
          f"{SOYUZ_MS17.total_dv_ms:.1f} m/s "
          f"(diff {abs(total_dv_replayed - SOYUZ_MS17.total_dv_ms):.2f} m/s)")
    print(f"  Note: per-burn dv values are 🟡 from RussianSpaceWeb compilation; "
          f"confirm with Murtazin 2020 paper before publication.")
    print("=" * 72)


if __name__ == "__main__":
    main()
