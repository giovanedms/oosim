# OOSim — Final Headline Results Summary
_Generated 2026-07-01 22:00 UTC_

Companion summary for the IAC 2026 paper `IAC-26,C2,3,6,x112752` and
the OOSim release on `github.com/giovanedms/oosim`.

## v0 → v3 architectural cascade

| Version | Description | Success rate | p95 pos err |
|---|---|---|---|
| v0 | Open-loop QP single-shot (cosmetic) | 100% | 0.4 mm |
| v1 | Closed-loop MPC, hard terminal | **0%** | 1080 mm |
| v2 | UKF + closed-loop MPC, hard terminal | **0%** | 1027 mm |
| v3 | UKF + soft terminal cost + gentler control | **100%** | 10.3-153.1 mm |

Architectural lesson: hard terminal constraints in receding-horizon MPC 
cause sub-optimization (each iteration commits to a plan it discards). 
Soft terminal cost replaces the constraint with a quadratic penalty, 
allowing intermediate states to hover near the envelope while the 
multiplicity of MPC iterations drives convergence inside.

## Statistical sensitivity (v3, 500 trials per cell, parallel)

| 3σ noise [mm] | latency [ms] | success | CI lower | p95 pos [mm] | bootstrap CI |
|---|---|---|---|---|---|
| 5 | 50 | 500/500 | 0.993 | 10.3 | [9.8, 10.9] |
| 5 | 100 | 500/500 | 0.993 | 13.5 | [13.1, 13.9] |
| 5 | 200 | 500/500 | 0.993 | 18.0 | [17.5, 19.0] |
| 50 | 50 | 500/500 | 0.993 | 60.4 | [56.0, 63.9] |
| 50 | 100 | 500/500 | 0.993 | 58.3 | [55.4, 61.1] |
| 50 | 200 | 500/500 | 0.993 | 60.6 | [58.8, 62.2] |
| 200 | 50 | 500/500 | 0.993 | 153.1 | [144.7, 161.9] |
| 200 | 100 | 500/500 | 0.993 | 145.9 | [138.7, 155.4] |
| 200 | 200 | 500/500 | 0.993 | 153.1 | [142.8, 160.4] |

## Failure boundary (v3, 400 trials per cell — pushed past the plausible envelope)

Extends the sensitivity sweep to 1.5 m 3σ noise and 2 s latency to locate where
v3 finally breaks (scripts `25_failure_boundary.py`, `26_failure_boundary_figure.py`;
CSV `failure_boundary_*.csv`; figure `fig12_failure_boundary.png`).

| 3σ noise [mm] | 100 ms | 500 ms | 1000 ms | 2000 ms |
|---|---|---|---|---|
| ≤200 (plausible band) | 100% | 100% | 100% | 100% |
| 400 | 100% | 99.5% | 97.8% | 9.2% |
| 600 | 97.5% | 96.8% | 70.8% | 0.5% |
| 800 | 90.8% | 83.0% | 46.5% | 0% |
| 1000 | 85.5% | 76.0% | 33.2% | 0% |
| 1500 | 60.2% | 46.5% | 23.2% | 0% |

Headline: 100% success across the entire realistic sensor band (≤200 mm 3σ) at
every latency up to 2 s. First sub-100% cell at 400 mm 3σ (≈8× a cm-level ranging
sensor). Degradation is joint noise×latency, not noise alone; every failure is a
terminal state outside the capture box (QP infeasibility never observed).

## Per-mission validation (v3 pipeline, 14 hardcoded missions)

| Mission | Sim total dv [m/s] | Pub total dv [m/s] | Rel err [%] | Pos err [mm] | Inside env? |
|---|---|---|---|---|---|
| SOYUZ_MS17 | 111.18 | 110.70 | 0.43 | 31 | ✅ |
| APOLLO11_LM_RDV | 1770.69 | 1770.00 | 0.04 | 30 | ✅ |
| ATV1_JULES_VERNE | 0.48 | 0.00 | n/a | 17 | ✅ |
| HTV7_KOUNOTORI | 0.49 | 0.00 | n/a | 34 | ✅ |
| CYGNUS_NG21 | 0.50 | 0.00 | n/a | 35 | ✅ |
| MEV1_INTELSAT901 | 0.49 | 0.00 | n/a | 49 | ✅ |
| ETSVII | 0.49 | 0.00 | n/a | 37 | ✅ |
| CREW_DRAGON_DM2 | 0.48 | 0.00 | n/a | 46 | ✅ |
| CARGO_DRAGON_CRS21 | 0.48 | 0.00 | n/a | 21 | ✅ |
| ASTP | 28.48 | 28.00 | 1.71 | 21 | ✅ |
| STS71_MIR | 0.48 | 0.00 | n/a | 31 | ✅ |
| SHENZHOU9 | 0.48 | 0.00 | n/a | 26 | ✅ |
| TIANZHOU1 | 0.48 | 0.00 | n/a | 21 | ✅ |
| ELSAD | 0.49 | 0.00 | n/a | 27 | ✅ |

## Soyuz MS-17 end-to-end pipeline result

- **Phasing dv (replayed):** 110.70 m/s
- **Terminal dv (simulated):** 480.9 mm/s
- **Total OOSim dv:** 111.181 m/s
- **Published total dv:** 110.7 m/s
- **Relative error:** 0.43%
- **Terminal pos error:** 30.9 mm
- **Source DOI:** 10.1016/j.actaastro.2020.04.032

## Reproducibility

All scripts in `experiments/scripts/` reproduce the headline numbers.
Required environment: Python 3.11+, numpy, scipy, matplotlib, cvxpy, ecos, sgp4.
Install via `pip install -e .[dev]` from the repo root.

Bibliography in `dataset/bibliography.bib` validated via Crossref REST API.
Mission data in `dataset/missions.csv` (50 missions, RPOD-50 dataset).

## Cite as

```bibtex
@inproceedings{morais2026oosim,
  author = {Morais, Giovane and Milagre da Fonseca, Ijar and Villani, Em\'ilia},
  title = {Computational Simulation of Rendezvous and Robotic Berthing for 
           On-Orbit Servicing: Validation Against Operational Mission Data},
  booktitle = {77th International Astronautical Congress (IAC 2026)},
  address = {Antalya, T\"urkiye}, year = {2026}, note = {IAC-26,C2.3.6}
}
```