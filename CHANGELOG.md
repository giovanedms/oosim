# Changelog

All notable changes to OOSim documented per commit on the `main` branch.

## 0.2.x — F1 (Apr 2026)

### a007324 — F1+++++++++ — SGP4 anchor + per-mission grid + final summary
- New scripts 19/20/21: SGP4 ISS anchoring with figure 10, per-mission grid figure 11, FINAL_SUMMARY.md aggregator
- Section 4.4.1 expanded with the 4500-trial / Clopper-Pearson 0.993 numbers

### 2209b49 — F1++++++++ — Lambert Izzo + chance-constrained stub + 4500-trial parallel sweep
- New `oosim/utils/lambert_izzo.py` (Izzo 2015 simplified)
- New `oosim/targeting/chance_constrained.py` (Blackmore-Ono helper + stub)
- Script 18 parallel sweep, 4500 trials, ~10 min wall time, all cells 500/500 success, lower CI 0.993
- 50 tests pass + 1 xfail + 1 xpass

### 95ed9d5 — F1+++++++ — Manuscript Section 5+5.2 with REAL bootstrap CI numbers; revised arch fig
- Section 5.2 Table with 11/11 per-mission v3 results
- Section 5.4 Table with bootstrap CI numbers
- Figure 1 architecture diagram revised for v3 pipeline (UKF + soft-cost QP)
- main.tex includes all 9 sections + acknowledgments

### fbd9877 — F1++++++ — 11/11 missions success + bootstrap CI 100/100 central + cascade fig
- Per-mission validation v3: 11/11 inside envelope (Soyuz MS-17 0.43% err, Apollo 11 0.04% err, ASTP 1.71% err)
- Bootstrap sensitivity: 100/100 central + 30/30 surrounding cells, Clopper-Pearson lower 0.964
- Cascade figure 09 (visual v0 → v3 progression)
- Lambert Izzo API stub

### ddc3620 — F1++++ — SOFT TERMINAL COST resolves the v1/v2 negative results — 100% MC success
- **Architectural fix:** new `terminal_mode="soft"` in QP avoids hard-constraint sub-optimization
- v3 Monte Carlo: 100% success across 9 noise/latency cells (5/50/200 mm × 50/100/200 ms)
- Diagnostic script 09 bisected the failure: condition D (single-shot QP) gave 100%/0.2 mm
- Section 5.4 reorganized as v0/v1/v2/v3 narrative

### 6289674 — F1+++ — UKF state estimator + 4 missions + Lambert v1 robust + Section 8
- New `oosim/targeting/ukf.py` (Julier-Uhlmann UKF, 6-dim relative state)
- 4 new mission parsers: Crew Dragon DM-2, Cargo Dragon CRS-21, ASTP, STS-71
- Lambert v0 → v1 refactor (Vallado universal-variable, robust bracket)
- Section 8 NEW: Acknowledgments + AI Usage Disclosure (per IAF requirements)

### 6854460 — F1++ — Lambert/SGP4/frames_extra/polytope/vision; MPC tuning sweep
- 5 new utility modules
- 81-config × 20-trial MPC tuning sweep: ALL 0% success → architectural failure confirmed
- Section 2.7 NEW: comparison vs Basilisk/GMAT/Orekit/poliastro/astropy

### f3ff393 — F1+ — MPC closed-loop MC, 3 more missions, integration tests
- v1 closed-loop MC: 0% success exposed; v2 with UKF: 0% (8% improvement only)
- Mission parsers: Cygnus NG-21, MEV-1, ETS-VII
- Integration tests: full pipeline Hohmann → HCW → V-bar → QP capture

### 3c9e6d9 — F1 — Mission parsers (Apollo 11, ATV-1, HTV-7) + figures + Monte Carlo + sections 5-7
- 3 new mission parsers
- 4 architecture/V-bar/envelope/gain-scheduling figures
- v0 open-loop MC: 100% success across grid (cosmetic)
- Sections 5/6/7 drafts

### af2db2f — F1 launch — Capture envelope presets, missions parsers, full QP
- Da Fonseca-approved literature-documented capture envelope values
- CANADARM2_BERTHING / NDS_DOCKING / SSVP_DOCKING presets
- Soyuz MS-17 mission parser (3 burns, total 110.7 m/s)
- Generalized capture envelope from sphere to axis-aligned ellipsoid + V-bar corridor enforcement

### 77720ce — Add J2 secular perturbation, LVLH transforms, QP terminal targeting
- J2 secular rates (Vallado, Montenbruck-Gill formulas)
- ECI ↔ LVLH frame transforms with omega-coupling
- Functional CVXPY+ECOS QP solver

## 0.1.0 — F0 (Apr 2026)

### 329d046 — Initial commit: OOSim framework skeleton
- Modular architecture: phasing/proxops/attitude/targeting/utils/validation
- 9 modules + 1 test (Hohmann sanity vs Vallado Ch.6)

## Manuscript polish — UK English + anti-IA + scientific consistency (Apr 26 2026)

Manuscript files (`/dados/GoogleDrive/IAC-TURQUIA/manuscript/sections/*.md`) are versioned outside this git repo (Google Drive sync), but the changes are recorded here for traceability. Three parallel review agents were dispatched:

### Agent 1 — UK English audit
- 18 substitutions: formalizes→formalises, characterization→characterisation, maximization→maximisation, discretizing→discretising, quantization→quantisation, visualizes→visualises, sub-optimized→sub-optimised, internalize→internalise, amortize→amortise, generalization/generalizes→generalisation/generalises, MIT license (noun)→MIT licence, centerpiece→centrepiece, pioneering programs→pioneering programmes, Acknowledgments→Acknowledgements, catalogs→catalogues
- Section 4 had duplicate "## 4.5" — second one renumbered to "## 4.6"

### Agent 2 — Anti-IA pattern audit
- Removed/replaced critical IA-pattern phrases:
  - ✅ emoji in Section 5 LaTeX table → \checkmark (would have broken pdflatex compile)
  - "to (the best of) our knowledge" reduced from 4 to 2 occurrences (kept abstract + 1 background)
  - "headline figure" → neutral phrasing
  - "is the central methodological contribution" → "shows which architectural choices were decoys"
  - "Three caveats deserve explicit statement" → "Three caveats follow"
  - "is itself a methodological observation that we believe is under-discussed" → "is, we think, under-discussed"
  - "over-engineered continuous-PID assumptions ... absent from real flight systems" softened

### Agent 3 — Scientific consistency audit
- Cross-reference fixes:
  - "soft-terminal-cost reformulation introduced in Section 3.3" → "introduced in Section 5.4" (Sections 6 + 7 — was a forward-reference to non-existent content)
  - "across all v0 runs and across the v2 (UKF + MPC) runs" → "across all v3 runs (and across v0 as a baseline)" — v0/v2 had been failure cases
  - "16 cores" → "14 cores" (matches actual statistical_sweep_*.csv parallelism level)
  - "110.70 m/s" → "110.7 m/s" (consistent decimal precision with §5.1 narrative)
- CANADARM2 case consistency:
  - Prose mentions of CANADARM2 → Canadarm2 (preserve uppercase only for the CANADARM2_BERTHING preset name)
  - "below 30 cm (CANADARM2 envelope) or 10 cm (NDS envelope)" → "below 300 mm (Canadarm2 envelope semi-axis) or 100 mm (NDS envelope)"
  - "300-500 mm CANADARM2 envelope" → "300 mm Canadarm2 envelope semi-axis" (Canadarm2 has 0.5×0.5×0.3 m semi-axes; 300 mm is the most restrictive component)

### Remaining TODO items (require co-author review)
1. Section 3 has Eq (3.5) labelled twice (inscribed-ellipsoid AND QP objective). Renumbering the QP block to (3.5)–(3.10) is straightforward but conflicts with Sections 5/6 referencing "Constraint (3.6)" etc. — easier to fix at LaTeX template stage.
2. Section 3 promises Table 3.1 with capture-envelope numerical presets but the table is not inserted. Simple to add (CANADARM2_BERTHING / NDS_DOCKING / SSVP_DOCKING with semi-axes + v_max + omega_max).
3. Section 4 lists 12 reference missions; Section 5 Table 5.1 has 11 with only 6 overlap. Needs alignment — Section 5's list (which matches the actual hardcoded mission parsers in oosim/missions/) should become master.
4. Apollo 11 entry in Table 5.1: "LM RDV" with 1770 m/s should be confirmed — the rendezvous-only Δv is closer to 80 m/s; 1770 m/s includes the ascent insertion burn. Either rename to "LM ascent + RDV" or split the value.

## Opção C kickoff — option-c-physics branch (Apr 26 2026)

Branch `option-c-physics` started for the end-to-end physics-based simulator
extension. Goal: reproduce Soyuz MS-17 from insertion state to capture
without using published burns as input.

F2-real (4 weeks, 27/Apr–24/May): coupled physics simulator
F3-real (5 weeks, 25/May–28/Jun): mission reproduction (5 missions)
F4 writing → F5 review → F6 submit by 14/Sep/2026.

3 parallel Sonnet agents dispatched for F2-real Modules 1, 2 and 4.
Module 3 (13-dim coupled state) handled by Opus directly.
