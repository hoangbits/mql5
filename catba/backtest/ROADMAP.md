# CatBa Roadmap

Sequenced plan from research → validation → live. Each phase ends in a
GATE (a go/no-go decision). Repo-resident so any session resumes cold.

Legend: [x] done · [ ] todo · [~] in progress · (GATE) decision point.

---

## Phase 0 — Foundations  [DONE]
- [x] Fix lot-size bug (was ~16x too small; orders rejected).
- [x] Headless tester pipeline (JPY-denominated, GBPJPY-only, OnTester CSV).
- [x] Research framework: funnel S0–S5, false-negative defenses, literature
      criteria (DSR/PBO/BHY), hypothesis QUEUE + JOURNAL.
- [x] Validated sizing (equity-proportional, SL-independent) + ATR break-even.
- [x] Reference config is the EA default: decade +23.2% / 11% DD / worst -3%.
- [x] ~68 trials; ICT reversal toolkit shown unfit (GBPJPY is continuation).

## Phase 1 — Finish SMT investigation  [~ current]
- [ ] 1.1 LEAN test first: statistical divergence (GBPJPY vs synthetic
      GBPUSD x USDJPY residual), 2–3 params, TF in {M15,H1}, session open.
      Does ANY predictive signal exist across a param *neighborhood*?
- [ ] 1.2 (GATE-SMT-A) Plateau exists? NO -> kill SMT, journal, ICT closed.
      YES -> continue.
- [ ] 1.3 Full parameterized SMT harness EA (partner/TF/swing/session/
      strictness); tester auto-pulls partner data.
- [ ] 1.4 Grid sweep -> robustness surface; walk-forward; PBO/CSCV.
- [ ] 1.5 (GATE-SMT-B) Robust plateau + OOS survival + economic rationale?
      If not all three -> kill. If yes -> candidate signal.

## Phase 2 — Close the research queue  [ ]
- [ ] 2.1 H7 Po3/Judas as an *entry-location* refinement (not bias).
- [ ] 2.2 Coverage review vs taxonomy grid; test only under-covered,
      high-prior cells. Stop-condition: N consecutive kills, no new leads.
- [ ] 2.3 (GATE-RESEARCH) Declare search complete (multiple-testing wall)
      and freeze the signal set. Record final trial count + DSR on winner.

## Phase 3 — Harden the validated system  [ ]
- [ ] 3.1 Code-correctness pass on CatBa.mq5. Known latent issues to review:
      SL-check timer reuses checkEveryMinutes (line ~91); ORDER_FILLING_IOC
      not validated vs symbol filling mode; dead price_level block in
      update_sl_to_be; OnTrade empty. Fix real bugs, retest reference config.
- [ ] 3.2 Reduce Print() verbosity (guarded by a verbose flag) — the logs
      ballooned to 13 GB. Keep OnTester CSV output.
- [ ] 3.3 Final clean walk-forward of the reference config; compute PBO/DSR;
      write a one-page "system card" (edge, expectancy, DD, assumptions).
- [ ] 3.4 (GATE-SHIP) Config + code frozen, tagged in git (e.g. v1.0).

## Phase 4 — Forward-demo (S5)  [ ]  — the first REAL test
- [ ] 4.1 Open Darwinex demo near intended live size; attach reference config;
      enable Algo Trading; run continuously (VPS ideal).
- [ ] 4.2 Log every trade per FORWARD_DEMO.md; verify lots/SL/TP/BE/fills.
- [ ] 4.3 Cross-check trade-for-trade vs a backtest over the same window.
- [ ] 4.4 Run >= 4 weeks (mechanics), keep tracking for months (edge).
- [ ] 4.5 (GATE-DEMO) PASS = no bugs + slippage/spread in line with backtest.
      INVESTIGATE = any mechanical bug -> fix, re-demo. FAIL = costs eat edge.

## Phase 5 — Cautious live  [ ]
- [ ] 5.1 Start live at 0.5% risk. Mind the sub-$1700 min-lot over-risk.
- [ ] 5.2 Journal live trades; monthly compare realized vs expected
      (~2%/yr, ~11% DD at 0.5%). Watch for regime-year drag.
- [ ] 5.3 (GATE-SCALE) Only after a live quarter that holds up: consider
      1% risk (22% DD). Never 2%.

## Phase 6 — Ongoing / optional  [ ]
- [ ] 6.1 Quarterly re-validation; append new data to the walk-forward.
- [ ] 6.2 Generalization test: does the continuation+sizing edge hold on
      other JPY pairs (EURJPY, AUDJPY)? (portfolio diversification)
- [ ] 6.3 Regime research round 2 only if a NEW structural detector idea
      appears (2019 vs 2025 are different failure modes; no single gate
      caught both — open problem).
- [ ] 6.4 Infra: decide MCP (real password) vs manual login; VPS for 24/7.

---

## Decision gates summary
GATE-SMT-A/B (kill or keep SMT) · GATE-RESEARCH (freeze search) ·
GATE-SHIP (freeze code+config, tag v1.0) · GATE-DEMO (mechanics OK?) ·
GATE-SCALE (earn size-up with live proof).

## Guiding priors (don't forget)
- GBPJPY is continuation-dominated; reversal signals fight the prior.
- The edge is THIN (PF ~1.06). Risk management is the product, not the signal.
- More parameters = more overfit surface. Fewer knobs > clever knobs.
- The tester is truth; Python screens only rank candidates for it.
