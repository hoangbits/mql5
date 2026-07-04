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

## 2026-07-04 — H2b fade-switch + H13 router (S1 screens)
H2b W40: 52.5/+6.1 but 2019 still -2.3, new negs 2023/2026; W60 worse.
KILLED — trailing-window detectors lag ~2mo then whipsaw; regime needs a
STRUCTURAL signal, not recent-PnL. H13 router: 52.3/+2.7 < baseline;
all-sweep-days fade imports H3a trend-year losses. KILLED — dilution.
Round-1 tally: 19 variant-tests, 0 clean S1 passes, best standalone =
H1 band (53.8/+6.9, fails only 2025). Next: H5 (last D1 screen), then
intraday round (H4/H7/H8) which requires deep H1/M1 (grind + max-bars).

## 2026-07-04 — Framework amendment: false-negative defenses
Added scope-tagged kills, LEADS ledger, coverage-with-depth, near-miss
band, budgeted deep-dives, multi-lens metrics (RESEARCH.md §5).
Retro-applied: H3 -> KILLED@proxy(D1-c2c), spawns H3i (intraday sweep
fade at rejection w/ stop beyond raid extreme — tester-fidelity S1).
H2/H2b -> KILLED@mechanism (detector lag is inherent). H1 -> near-miss.
LEADS: (1) regime anti-correlation by year; (2) moderate-body carries
continuation edge; (3) non-sweep-day filter is cheap improvement.

## 2026-07-04 — FULL-DECADE BASELINE (tester, 2% risk, JPY-denominated)
2016->2026H1: net -75.7%, PF 0.92, maxDD 85.5%, 1684 trades, 5/11 years
positive. Catastrophic years: 2017 (-54%) and 2025 (-19% on shrunken
equity; -60% in fresh-start window). LEADS: (1) 2017 = second sweep-regime
strike, outside D1 autopsy window — regime recurs ~2x/decade; (2) 2020
lost -13% despite positive raw continuation — intraday mechanics leak
not visible at D1 proxy. Windowed runs (2024-start): +44% 2024 / -60%
2025 — engine is strong in-regime; defense is the whole game.
Root cause of grind failures found: /config with forward-slash path is
silently ignored; with backslashes all 5 windows ran in ~3 min (cache
was already complete from the first 80% download).

## 2026-07-04 — H12 sizing comparison (decade, tester)
Fixed 0.10 lot: +21.7%, PF 1.07, expectancy +206 JPY/trade, maxDD 14.1%,
worst year -5.1% — vs risk-2%: -75.7%, PF 0.92, maxDD 85.5%.
**Signal stream has positive gross expectancy; the risk-% sizing was
destroying it**: lot ∝ 1/SL-distance over-weights tight-SL trades (the
1:1-cap trades, which are the worst), and equity-compounding spirals
losing streaks. ANSWER (user Q): fixed lots decisively better for this
system as-is; forward tendency mildly positive (PF 1.07) but regime
years still negative (small). Spawned H12b: risk-% variants that break
the bad correlation (min-SL-width floor for sizing; risk on fixed base
not compounding equity; risk-% with lot cap).

## 2026-07-04 — H1 tester confirm + H12b isolation (trial count: ~25)
H1 band at S3 (fixed lots): PF 1.072 vs 1.065 plain — proxy gain does NOT
transfer; band only removes exposure (~-40% trades, DD 7.5% vs 14.1%,
profit +10% vs +21.7%). KILLED@tester as edge enhancer. (Fidelity
escalation catching a proxy false-POSITIVE.)
H12b(b) risk-2%-of-initial (no compounding): -65.7%, PF 0.96, maxDD 94%.
**ROOT CAUSE ISOLATED: inverse-SL-distance weighting is the poison, not
compounding.** Equal lots +21.7% vs same-signal 1/SL-weighted -65.7%.
Tight-SL trades come from the 1:1 R:R cap in place_trade -> H8 (remove/
replace SL cap) promoted to queue top; H12b(a) SL-floor sizing secondary.

## 2026-07-04 — H8a: SL-cap removal (trial count: ~29)
No-cap fixed lots: +21.0% PF 1.059 (≈ unchanged vs cap +21.7% PF 1.065).
No-cap risk-2%: -59.6% (vs -75.7%) — better but still catastrophic.
KILLED as fix hypothesis. **The 1:1 cap is not the toxin — inverse-SL
weighting is poisonous across the whole SL distribution**: entry-near-
pivot days (tight SL -> big lots) are systematically worse trade days.
SIZING ARC CONCLUSION (H12/H12b/H8a): equal or pure-equity-proportional
sizing only; never SL-distance-dependent sizing for this signal.
