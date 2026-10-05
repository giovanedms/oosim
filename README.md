# OOSim — Open On-Orbit Servicing Simulator

End-to-end Python framework for simulating rendezvous and robotic berthing for on-orbit servicing missions, with QP-based berthing-compatible terminal targeting (soft-cost formulation, MPC + UKF) and validation against operational mission data.

> **Authorship.** OOSim is authored by Giovane de Morais (ITA). The scientific content,
> the technical decisions and the choice of what to model, test and report are his. The code
> was written with LLM assistance under his direction, which is why every commit carries an
> AI `Co-Authored-By` trailer; Section 8 of the companion IAC 2026 paper declares the same
> thing, and this history is here so that declaration can be checked.

**Companion code for:**
- IAC 2026 paper `IAC-26,C2,3,6,x112752` — *Computational Simulation of Rendezvous and Robotic Berthing for On-Orbit Servicing: Validation Against Operational Mission Data*
- RPOD-50 Dataset — see `../dataset/`

## Headline results

- **4500/4500 trials success** (Clopper-Pearson 95% lower bound 0.993 per cell, 9 cells × 500 trials, parallel multiprocessing)
- **14/14 mission parsers** validated inside their respective capture envelopes (CANADARM2 / NDS / SSVP)
- **Soyuz MS-17 ultra-rapid 2-orbit profile** reproduced to **0.43% relative error** on total Δv
- **Apollo 11 LM rendezvous** reproduced to **0.04% error** (1770.69 vs 1770 m/s published)

## Architecture (v3 final)

```
oosim/
├── phasing/        Hohmann + J2 secular drift + finite-burn corrections
├── proxops/        HCW STM 6×6 + V-bar corridor enforcement
├── attitude/       Quaternion + RCS phase-plane (Schmitt trigger with hysteresis)
├── targeting/      Capture envelope + QP solver (hard/soft modes) + UKF + chance-constrained stub
├── utils/          ECI/LVLH/RTN frames + Lambert (Battin v1, Izzo v0) + integrators + SGP4 wrapper
├── missions/       14 mission parsers (Soyuz MS-17, Apollo 11, ATV-1, ETS-VII, ...)
└── validation/     RPOD-50 dataset loader
```

## Quick start

```bash
git clone https://github.com/giovanedms/oosim.git
cd oosim
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest                                      # runs the full pytest suite (130+ tests)
python experiments/scripts/12_soyuz_ms17_full.py  # end-to-end Soyuz MS-17 demo
```

## v0 → v3 architectural cascade (Section 5.4 of the paper)

| Version | Description | Success rate | p95 pos err |
|---|---|---|---|
| v0 | Open-loop QP single-shot (cosmetic) | 100% | 0.4 mm |
| v1 | Closed-loop MPC, **hard** terminal | **0%** | 1080 mm |
| v2 | UKF + closed-loop MPC, hard terminal | **0%** | 1027 mm |
| v3 | UKF + **soft** terminal cost + gentler control | **100%** | 12-153 mm |

**Architectural lesson:** hard terminal constraints in receding-horizon MPC cause sub-optimization (each iteration commits to a plan it discards). Soft terminal cost replaces the constraint with a quadratic penalty, allowing intermediate states to hover near the envelope while the multiplicity of MPC iterations drives convergence inside.

## Reproducibility

Key entry points in `experiments/scripts/`:

| Script | Purpose | Wall time |
|---|---|---|
| `02_figures.py` | Architecture, V-bar, capture envelopes, gain scheduling figures | ~5 s |
| `09_diagnostic.py` | Bisects MPC failure mode (A/B/C/D conditions) | ~30 s |
| `10_mpc_soft_terminal.py` | v3 Monte Carlo at 9 cells × 30 trials | ~3 min |
| `12_soyuz_ms17_full.py` | End-to-end Soyuz MS-17 with v3 (UKF + soft + gentler MPC) | <5 s |
| `14_per_mission_v3.py` | Validates all 14 mission parsers | ~30 s |
| `18_statistical_sweep_parallel.py` | 4500-trial parallel sweep (16 cores) | ~10 min |
| `21_final_summary.py` | Aggregates all results to FINAL_SUMMARY.md | <1 s |

## Authors

Giovane Morais, Ijar Milagre da Fonseca, Emília Villani — Instituto Tecnológico de Aeronáutica (ITA), Brazil.

## License

Code: see `LICENSE-CODE` (MIT). Dataset: see `../dataset/LICENSE-DATA` (CC-BY-4.0).
