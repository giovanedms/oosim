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

## F2-real progress — option-c-physics (May 3 2026)

Modules M1–M5 of F2-real complete and merged on `option-c-physics`:

- **M1** ECI propagator (Kepler + J2 secular) — Sonnet, commit `e2755e3`, 5/5 tests.
- **M2** ECI↔LVLH dynamic transform with omega-coupling — Sonnet, commit
  `06c1964`, 4/4 tests.
- **M3** Coupled 13-dim state propagator [r, v, quat, ω] — Opus, commit
  `13ad39f`, 8/8 tests. Body-frame thrust rotated to ECI via R(q); quaternion
  normalised inline + on output (DOP853 doesn't enforce constraint).
- **M4** Finite-burn correction (Vallado Eq. 6-79) — Sonnet, commit `c9645ef`,
  6/6 tests.
- **M5** Mission phasing reconstructor (Hohmann + finite-burn) — Sonnet,
  commit `8ea7696` (+ dead-import cleanup `8996176`), 6/6 tests. First
  integration layer: chaser+target ECI states in → burn sequence out.

ACT-JUDGE Gemini round 1 on M3 architecture (May 3 2026): quaternion math
verified correct (q=[0,0,0,1], ω=[0,0,1] → dq=0.5·[0,0,1,0]). Inline
re-normalisation finding empirically refuted — measured 543 vs 553 DOP853
steps (noise) and Baumgarte k=1 forces 19× more steps with no accuracy gain.
J2 in M3 deferred (architectural separation: M3 = terminal-handoff window
where J2 effect is sub-metre; M1 carries J2 secular for long phasing legs).
Drag and gravity-gradient torque deferred to A1 (negligible over 3.5 h
Soyuz timeline; RCS-dominated).

M6 (terminal-phase MPC handoff to coupled state) dispatched to Sonnet.
M7 (Soyuz MS-17 smoke test) blocks on operator-supplied TLE 2020-10-14
and Soyuz post-insertion state.

## F2-real wrap + F3-real complete — option-c-physics (May 3 2026, late)

Same-day extension after the F2-real M1-M5 entry above.

### F2-real closure (M6, M7)

- **M6** Terminal-phase MPC handoff to coupled state — Sonnet, commit
  `74947bb` (+ dead-import cleanup `0cd2bc4`), 4/4 tests. Stateful
  `TerminalMPCController` injects into the M3 RHS via `thrust_callback`,
  solves the existing `qp_terminal_target` QP every `qp_dt` seconds and
  applies the first impulse as a finite-duration body-frame thrust.
  Finding: spec defaults (qp_dt=20s, h=15) diverged 50→178 m on a 50 m
  approach; relaxed to qp_dt=150s, h=3 (used in M7).
- **M7** Soyuz MS-17 end-to-end smoke pipeline — Sonnet, commit `227dc42`,
  6/6 tests. First M5+M6 wiring, with placeholder ISS/Soyuz states. Smoke
  output: phasing 127 m/s + terminal 0.2 m/s = 127 m/s total vs Murtazin
  reference ≈110.7 m/s; mission duration 236 min vs ultra-rapid ≈210 min.
  v1 has a documented hold-point hack since M5 v1 doesn't do
  phase-matching (chaser ends ~670 km off after Hohmann).

### F3-real (kicked off and largely complete same day)

Pipeline grew to **M5 → M8 → M9 → M6**:

- **M8** Phasing-orbit drift loop (Vallado §6.6.1) — Sonnet, commit
  `f68171d` + docstring fix `d7b46c5`, 7/7 tests. Closes the M5 v1
  phase-matching gap with a co-elliptic two-impulse maneuver across
  k drift orbits. **Sonnet caught a sign error in Opus's spec**
  (`T_phase = T_target × (1 - Δθ/(2πk))` should be `1 + Δθ/(2πk)`):
  spec formula left 1185 km residual; corrected formula 0 m. Re-derived
  from Vallado: chaser behind (Δθ<0) needs smaller orbit (faster) to
  catch up, hence T_phase < T_target.
- **Validation framework** (`oosim/validation/mission_runner.py`) —
  Sonnet, commit `930cda3`, 6/6 tests. `MissionScenario` dataclass +
  `validate_mission()` runner with tier-specific tolerances (Tier A
  published ±5%, Tier B reverse-engineered ±20%, Tier C qualitative).
  Internally split into `types.py` + `mission_runner.py` to avoid
  circular imports with `oosim/scenarios/`.
- **M9** HCW two-impulse approach-corridor entry (Curtis §7.4) — Opus,
  commit `41187e6`, 5/5 tests. Closes a gap discovered debugging ATV-1:
  when M8 perfectly colocates chaser (~0 m), M6 has nothing to optimise
  from and drifts kilometres in 400 s due to HCW-vs-Kepler mismatch
  amplifying small impulses. M9 places chaser at a known LVLH hold
  point (default [0, -50, 0] m on V-bar) before M6 takes over. Also
  retunes M6 default from qp_dt=150s,h=3 to qp_dt=60s,h=5 — empirically
  stable across orbital inclinations.

### F3-real mission scenarios (4 missions, all Tier B placeholders)

| Mission | Commit | sim Δv | ref Δv | err | dist | Verdict |
|---|---|---|---|---|---|---|
| ATV-1 Jules Verne | `930cda3` | 56.6 m/s | 120 | -52.8% | 16.4 m | FAIL |
| HTV-7 Kounotori 7 | `1e027e7` | 101.1 | 150 | -32.6% | 18.1 m | FAIL |
| Crew Dragon DM-2 | `d8c6d62` | 146.2 | 90 | +62.5% | 17.4 m | FAIL |
| Cygnus NG-21 | `9aeb363` | 111.4 | 120 | **-7.2%** | 17.2 m | **PASS** |

The pipeline converges in all four (terminal_distance 16-18 m); 1/4 PASS
on Δv reflects placeholder mis-calibration, NOT simulator error. NG-21
PASS suggests other missions would also pass with real ESA / JAXA / NASA
primary docs replacing the Tier B reverse-engineered estimates.

### Status going into F4

- **129 tests pass**, 0 unexpected failures.
- 18 commits on `option-c-physics`, all pushed to GitHub.
- Decision-gate F2 (24/May) effectively reached 21 days early.
- Operator action items still blocking Tier A: TLE for ISS at
  2020-10-14T05:45 UTC (space-track.org) + Murtazin (2020) PDF for
  rigorous Soyuz MS-17 reproduction.
- F4 (manuscript rewrite of Sections 3/4/5) is the next planned phase.
