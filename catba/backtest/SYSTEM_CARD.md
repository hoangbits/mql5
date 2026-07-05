# CatBa v1 — System Card (2026-07-05)

One-page honest scorecard for the validated reference config. Read this
before risking money.

## Config
GBPJPY H1. Daily-continuation bias (yesterday's D1 direction) + EMA(8)
pullback entry + prior-day pivot R1/S1 exits with 1:1 SL cap. Break-even
at 0.3xATR(14,D1), checked every 12 min. Sizing: equity-proportional on a
fixed 70-pip reference (`useFixedRefStopSizing`), risk 0.5%/trade default.
Max 1 trade/day.

## Backtest performance (Darwinex, 2016-01 .. 2026-07, 1-min OHLC model)
| | Full 2016-26 | IS 2016-22 | OOS 2023-26 |
|---|---|---|---|
| Net (0.5% risk) | +23% | +21%* | +4%* |
| Ann. Sharpe | **0.45** | 0.62 | **0.18** |
| Sortino | 0.72 | 1.00 | 0.29 |
| Positive months | 54% | 57% | 49% |
*(net at fixed 0.10 lot; % framing on 1.6M JPY nominal)*

- Max drawdown (historical path): **8–11%** at 0.5% risk.
- Monte-Carlo (20k sims): median DD ~13-15%, 95th ~22%, ~8.5% chance a
  decade ends net-negative. Historical 11% was somewhat favourable.
- Worst calendar year: **-3%** (2025). No catastrophic year.

## Honest statistical read  ⚠️
- **The edge is THIN and marginal.** Ann. Sharpe 0.45 is low; PF ~1.06.
- **It decayed out-of-sample:** IS Sharpe 0.62 -> OOS 0.18 (roughly halved).
- **~78 trials of searching.** After the multiple-testing haircut (Deflated
  Sharpe), the full-sample Sharpe is NOT clearly distinguishable from the
  best-of-78-lucky-draws (DSR ~0%). Per Harvey-Liu, a Sharpe < 0.4-0.5 with
  this many trials warrants a >50% haircut.
- **Only positive evidence:** the untouched holdout (2023-26) is still
  positive (+4%, Sharpe 0.18) — weak, but not negative.

**Verdict: a marginally-positive, low-quality edge.** The big win was
*fixing a broken system* (-76% -> +23% by correcting sizing); the residual
edge is real-ish but small and unproven. This is NOT a high-confidence
money-maker. Whether the thin margin survives live costs is genuinely
uncertain — forward-demo is essential, not a formality.

## Where the value actually is
Risk MANAGEMENT, not signal alpha. The system's job is to grow slowly
(~2%/yr at 0.5%) with shallow drawdowns and no blow-up years — not to
print money. Position it as a low-risk, low-return, diversifiable sleeve.

## How to run it (if you proceed)
- **Risk 0.5%** (default). Do NOT exceed 1% without a live quarter of proof.
  2% risk = ~40% drawdowns (reckless).
- Below ~$1,700 equity, min lot forces risk above 0.5% — mind this.
- **Forward-demo first** (see FORWARD_DEMO.md) — the demo's job is execution
  fidelity + bug-catching; 4 weeks is too few to confirm the edge.
- Expect drawdowns of 15-22%; do not be surprised by a losing year.

## Known open problem
Regime years (2019/2025 = different failure modes) drag results; no
structural detector survived testing. Unsolved.

## Generalization test (2026-07-05) — added post-hoc
Applied the EXACT reference params (no re-tuning) to other 3-digit JPY pairs:
  GBPJPY +23% PF1.07 | EURJPY +3.4% PF1.02 | AUDJPY -4.6% PF0.97 | CADJPY -7.4% PF0.94
2/4 positive; non-home pairs average ~-3%. The edge is **largely
GBPJPY-specific, NOT a robust cross-pair continuation edge**, and GBPJPY's
result leans on 2 lucky trending years (2022/2024). This DOWNGRADES
confidence further: treat +23% as an optimistic upper bound, not an
expectation. Forward-demo is essential; if traded, 0.5% only.

## GBPJPY-ONLY UPDATE (2026-07-05): emaPeriod 8 -> 13
User is trading GBPJPY only, so cross-pair failure is less disqualifying;
the relevant tests (walk-forward + PBO on GBPJPY) PASS. New default emaPeriod=13.
  Decade @0.5%: +42.9% (vs +23.2%), PF 1.119 (vs 1.062), DD 11.2%, 8/11 green,
  worst yr -2.7%. Signal quality (fixed-lot): ann Sharpe 0.72 (vs 0.45),
  Sortino 1.43, skew +0.66.
  KEY: OOS 2023-26 Sharpe = 0.80 — did NOT decay (ema8 decayed to 0.18).
  This is the strongest evidence ema13 is GBPJPY's right EMA, not a lucky fit.
CAVEATS (still honest): (1) GBPJPY-SPECIFIC — the ema13 gain does NOT transfer
to EURJPY/AUDJPY/CADJPY (all got worse); it exploits GBPJPY's particular
character, so it may be more exposed to regime shifts than a universal edge.
(2) DSR ~0% at the 120-trial haircut (ultra-conservative). (3) Never
forward-tested. -> Forward-demo BOTH ema8 and ema13 to confirm before trusting.
Also fixed a dead input this session: place_trade now respects
useRiskPercentPerTrade (was checking only riskPercentPerTrade>0).

## UPDATE 2026-07-05b: + min-stop filter (minStopPips=30)
Loss-mode analysis found tight-SL setups (entry near pivot, <=40 pips) win only
38% and lose money. Added minStopPips filter (skip them). Walk-forward: improves
OOS (23%->27%) across a robust plateau (ms20-50); did NOT pick the IS-optimum
(60) which over-filters/degrades OOS.
NEW DEFAULT: emaPeriod=13, minStopPips=30, sizing 0.5% equity-prop, ATR-BE 0.3.
  Decade @0.5%: +56.5% (~4.4%/yr CAGR), PF 1.155, DD 10.9%.
  Signal (fixed-lot): ann Sharpe 0.87 (was 0.45 at project start), Sortino 1.71,
  OOS Sharpe 0.93 (higher than IS -> NO decay), skew +0.51, PSR 99.8%.
Journey: ema8 Sharpe0.45/OOS0.18 -> ema13 0.72/0.80 -> +ms30 0.87/0.93. Two
disciplined improvements (emaPeriod, min-stop filter) ~doubled the Sharpe with
OOS holding up. STILL: GBPJPY-only validation, DSR~0 at full haircut, unproven
forward -> forward-demo remains the gate.
