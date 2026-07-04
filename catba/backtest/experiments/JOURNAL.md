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
