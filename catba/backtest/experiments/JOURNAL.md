# Experiment journal (append-only; kills included)

## 2026-07-04 — Lot-size bug (pre-research finding)
`CalculateLotSize` divided by tickSize*tickValue (dimensionally wrong) +
redundant USDJPY hack → lots ~16× small → 0.00 at 0.2% risk → orders
rejected → historical "results" meaningless. Fixed in `2bf4b1a`,
verified in tester (stop-out ≈ 2% equity as intended).
**Lesson: every historical impression of this EA predates correct sizing.**

## 2026-07-04 — Baseline at correct sizing (partial window)
2025-06→2026-07, 2% risk: **−37.9%**, PF 0.76, maxDD 54%, 176 trades.
Current logic has negative edge at proper size. Full-decade baseline
pending (M1 cache grind in progress).

## 2026-07-04 — Bias autopsy (D1 2018-10→2026-07, 1998 days)
Continuation: 52.2% / +4.9 pips avg (thin, ≈ spread). Killer years are
regime: 2019 (47.1%), 2025 (45.7%) anti-continuation; 2022 strong trend.
**Body filter is inverted**: ≥0.28 → 52.1%; ≥0.50 → 51.4%; ≥1.00 → 51.0%.
Big bodies mean-revert. → spawned H1 (cap/invert), H2 (regime gate),
H3 (sweep reversal aligns with mean-reversion finding).

## 2026-07-04 — H1 body cap/inversion (S1 screen)
Best band 0.10<=|body|<=0.60: 53.8% / +6.9 pips (vs 52.2/+4.9 baseline),
neg years: 2025 only; rescues 2019 (-2.0 -> +2.4); improves/ties 8/9 years.
FAILS 2025 clause (-3.6 -> -7.1). Verdict: PARTIAL — not standalone;
composition candidate. Insight confirmed: edge lives in MODERATE bodies;
floor-only filter is wrong shape.

## 2026-07-04 — H2 trailing win-rate regime gate (S1 screen)
All 6 variants (W=40/60/90 x thr=0.50/0.55): 2019 negative in every one;
tight variants poison 2026 (to -29 pips/day). Verdict: KILLED.
Lesson: trailing win-rate gate LAGS regime turns — shuts after damage,
reopens after the run. Spawned H2b (fade-switch below 0.45) as new
pre-registration.

## 2026-07-04 — H3 PDH/PDL sweep-reversal (S1 screen)
H3a sweep-only: 50.6% / -1.3, neg 4 years -> KILLED standalone.
H3b combined: 51.7% / +3.6 < baseline -> KILLED.
**DISCOVERY: yearly anti-correlation.** Sweep-reversal wins exactly where
continuation loses (2019 +11.7 vs -2.0; 2025 +6.7 vs -3.6; and mirror in
2020/2022/2024). Market alternates continuation-regime vs sweep-regime
years; killer years ARE sweep years. Continuation on non-sweep days only:
+6.0 vs +4.9 baseline. -> H2b promoted; H13 router pre-registered.
