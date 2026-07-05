# CatBa Edge Research Framework

The problem: a huge space of candidate edges, two failure modes —
**missing a real edge** (under-exploration) and **shipping a fake one**
(overfitting / multiple-comparisons). Process beats cleverness on both.

## 1. The taxonomy grid (so we never *miss* an edge)

Every trading idea is a cell in this grid. Enumerate per dimension; test
dimensions independently first, then compose survivors greedily.

| Dimension | Candidates |
|---|---|
| **Bias signal** | D1 continuation (current) · PDH/PDL sweep reversal · D1 FVG displacement · Po3/Judas · weekly-open premium/discount · SMT (GBPUSD) |
| **Regime gate** | rolling 60d continuation win-rate · ATR level/slope · ADX(D1) · body-size cap (inverted filter!) · day-of-week |
| **Entry timing** | any hour (current) · London KZ 02–05 NY · NY KZ 07–10 · both variants 08:30–11 |
| **Entry location** | EMA−offset pullback (current) · daily-open retrace (Po3) · H1 FVG retrace · OTE 62–79% |
| **Exit/stop** | pivot R1/S1 + 1:1 cap (current) · ATR-multiple SL/TP · trail vs BE-lock · time-stop end-of-day |
| **Sizing** | risk-% (current) · fixed lot · risk-% with DD throttle |

Rule: **one dimension changes per experiment.** Composition only between
stage-3 survivors.

## 2. The funnel (so nothing *fake* survives)

Every hypothesis passes these gates in order. Any failure → KILLED, with
the reason journaled. No resurrection without new evidence.

- **S0 Pre-register.** Write the exact rule, its parameters, and the
  *predicted* effect in QUEUE.md **before** running anything.
- **S1 Fast screen** (Python, D1/H1, minutes). Keep iff: beats baseline
  (52.2% / +4.9 pips) overall **and** is not negative in ≥7 of 9 years
  **and** helps or is neutral in the killer years (2019, 2025).
- **S2 Robustness.** Perturb each parameter ±30%: effect must survive on a
  *plateau*, not a knife-edge peak. Check trade count ≥ ~100/screen.
- **S3 Tester confirm** (MT5, real spread, JPY-denominated, Model=1).
  Keep iff per-year table still holds with costs and proper sizing.
- **S4 Walk-forward.** Optimize 2016–2022 only; validate untouched
  2023–2026. Keep iff OOS is positive and DD acceptable.
- **S5 Forward demo** (weeks, demo account) before real money.

## 3. Discipline rules

1. **Count every test.** Each S1 run is one draw from the luck lottery; ~1
   in 20 random rules "works" at p=0.05. Consistency-across-years is our
   practical multiple-comparisons guard — totals can be lucky, nine
   separate years rarely are.
2. **Effect size over significance.** +0.5 pip/day edges die to spread.
   Demand margins that survive ~3 pips of cost.
3. **Holdout is sacred.** 2023–2026 results are looked at only at S4, and
   each hypothesis gets ONE look. Repeated peeking = the holdout silently
   becomes training data.
4. **One change at a time.** If two things changed, the result attributes
   to neither.
5. **Journal everything, including kills.** A killed hypothesis with a
   reason is knowledge; an unlogged one will be re-tested and re-killed
   forever.
6. **Prefer inversion of a measured effect over invention.** (E.g. the
   body filter measurably hurts → test the cap/inversion before exotic
   new signals.)
7. **The tester is the source of truth**; Python screens only rank
   candidates for it.

## 4. Long-loop session protocol (autonomous research mode)

State lives in the repo, not in the chat context — any session resumes
cold:

- `experiments/QUEUE.md` — prioritized, pre-registered hypotheses (S0).
- `experiments/JOURNAL.md` — append-only results, incl. kills.
- Loop iteration = pop top of QUEUE → implement screen → run → append
  JOURNAL entry (verdict + per-year table) → push follow-ups to QUEUE →
  `git commit` → next.
- Long-running tester passes / M1 cache grinds run in the background
  between iterations.
- Every ~5 experiments: a review pass — re-rank QUEUE using what was
  learned, check we're not starving a whole dimension (coverage check
  against the grid above).
- Stop conditions: QUEUE empty, or N consecutive kills with no new
  follow-ups (space exhausted at current knowledge).

## 5. False-negative defenses (don't kill real edges with shallow tests)

The funnel above is biased to kill; these rules bound what a kill means.

1. **Scope-tagged kills.** `KILLED@proxy(<measurement>)` = dead at that
   fidelity only, retestable ONLY at deeper fidelity (never a same-level
   rerun). `KILLED@mechanism` = the causal story itself falsified.
2. **LEADS ledger.** Killed hypotheses that showed systematic structure
   (e.g. H3's regime anti-correlation) are recorded as leads; pure-noise
   kills are buried.
3. **Coverage-with-depth.** The taxonomy grid records the fidelity each
   cell was tested at (D1-proxy / H1-proxy / tester). A cell is not
   "covered" above its tested depth.
4. **Near-miss band.** Results within noise of the pass bar are flagged
   for composition + one deeper-fidelity look, not binarized to dead.
5. **Budgeted deep-dives.** Every ~5th loop iteration re-tests one
   KILLED@proxy item at tester fidelity.
6. **Multi-lens metrics.** Screens report win%, mean, median, and
   top-day concentration — fat-tailed edges die under win%/mean alone.

## 6. Literature-verified criteria (deep-research 2026-07-04/05; votes 3-0 unless noted)

Sources: Bailey & López de Prado, "The Deflated Sharpe Ratio" (SSRN
2460551); Bailey, Borwein, López de Prado, Zhu, "The Probability of
Backtest Overfitting" (SSRN 2326253); Harvey & Liu, "Backtesting"
(SSRN 2345489).

**Adopted as hard rules:**
1. **N-trials is a mandatory field.** A result reported without its trial
   count is uninterpretable (worthless, per B&LdP). Our JOURNAL already
   carries a running trial count — every future entry must too.
2. **The bar rises with N.** E[max SR] across N skill-less trials grows
   with N and trial variance (closed-form EVT approximation exists). A
   "best of 42 trials" must clear a far higher bar than a single test.
3. **Holdout reuse is quantified poison.** ~20 uses at 95% confidence
   makes a false positive EXPECTED. Our one-look-per-hypothesis rule is
   literature-backed; decade-spanning runs silently consume holdout looks
   — log them.
4. **PBO as selection metric.** P(IS-optimal config underperforms the
   MEDIAN config OOS). Sobering benchmark: an 8,800-combination search on
   a PURE RANDOM WALK produced IS Sharpe 1.27 with PSR-stat 2.83 (>99%
   "significant") while PBO was 55% — single-test significance can fully
   pass on noise. When we run MT5 optimizer sweeps, compute PBO across
   the pass matrix before believing the winner.
5. **Nonlinear haircut (vote 2-1).** SR < 0.4 → discount >50% (usually to
   insignificance); SR > 1.0 → ≤25%. Our PF≈1.07 results live in the
   heavy-discount zone: treat as "promising, unproven," never ship-ready.
6. **BHY/FDR over Bonferroni** for multiplicity correction in trading
   research (Bonferroni's FWER control manufactures false negatives).

**Plausible, verification quota-killed (treat as leads, not rules):**
lenient-IS-then-OOS-intersection funnel for false negatives (Harvey &
Liu); MinBTL < 2·ln(N)/E[maxSR]² minimum backtest length; CPCV > walk-
forward at preventing false discoveries; White's Reality Check / Hansen
SPA as formal best-of-universe tests.

## 7. Cross-instrument generalization (orthogonal to walk-forward)
Walk-forward and PBO/CSCV validate only across TIME on the SAME instrument,
so they CANNOT catch instrument-specific overfitting. A parameter fitted to
one symbol's character stays stable across that symbol's time periods and
PASSES walk-forward + PBO while being pure curve-fit. ALWAYS add a cross-
instrument check: apply the optimized config unchanged to related instruments.
A real edge shows some positive transfer; a config that improves the home
symbol while degrading related ones is overfit. (Evidence H17: ema21 passed
walk-forward OOS+22.6% and PBO 8.3% on GBPJPY but made EURJPY/AUDJPY/CADJPY
all worse -> KILLED.)
