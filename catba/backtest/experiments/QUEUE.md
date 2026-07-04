# Hypothesis queue (pre-registered, priority order)

Format per entry: rule (exact), parameters (fixed BEFORE running), prediction.
Status: QUEUED → S1..S5 / KILLED(reason).

---

## H1 — Body-size filter inversion  [QUEUED]
Rule: replace `|body| >= minPips` with `minCap <= |body| <= maxCap`, test
maxCap ∈ {0.60, 1.00, 1.50} with minCap=0 and minCap=0.10.
Prediction: removing/capping the filter beats the current 0.28 floor
(measured: bigger bodies → weaker continuation).
Basis: bias_autopsy 2026-07-04.

## H2 — Rolling regime gate on continuation  [QUEUED]
Rule: trade continuation bias only if trailing 60-day continuation
win-rate > 50% (also test 55%, and window 40/90). Else flat.
Prediction: rescues 2019/2025 (anti-continuation years), small cost in
trend years. THE top candidate from the autopsy.

## H3 — PDH/PDL sweep-reversal bias (ICT turtle soup)  [QUEUED]
Rule: yesterday traded through prior-day high (low) AND closed back
inside prior-day range → today bias = SELL (BUY). No sweep → no trade
(variant b: fall back to continuation).
Prediction: positive esp. in 2019/2025; complements H2.

## H4 — Killzone entry window  [QUEUED]
Rule: allow entries only during London KZ 02:00–05:00 NY (variant b:
NY KZ 07:00–10:00; variant c: 08:30–11:00; variant d: London+NY).
Requires server-clock→NY mapping calibrated from weekend gaps first.
Prediction: edge concentrates in KZs; filter cuts losers > winners.

## H5 — D1 FVG displacement bias  [QUEUED]
Rule: bullish D1 FVG (high[2] < low[0]) unfilled → BUY bias while price
above gap 50%; symmetric for bearish. Min gap ∈ {0, 0.10, 0.20} JPY.
Prediction: modest improvement over raw continuation; fewer, better days.

## H6 — ATR-scaled thresholds  [QUEUED]
Rule: addPipsToEMA, DistanceToTriggerBE, add_pip_to_sl, body caps as
multiples of ATR(14,D1) instead of fixed JPY amounts.
Prediction: single param set generalizes across 2016-quiet vs 2022-wild
regimes; prerequisite for honest decade-wide optimization.

## H7 — Po3/Judas entry  [QUEUED]
Pre-registration (fixed now): daily open = 00:00 New York. Judas =
counter-bias excursion ≥ 0.15×ATR(14,D1) below (above) daily open during
02:00–05:00 NY. Entry on return through daily open, bias from H2/H3
winner. Prediction: better entry price than EMA pullback; fewer trades.

## H8 — Exit redesign: ATR stops vs pivot+1:1cap  [QUEUED]
Rule: SL = 1.0×ATR(14,D1), TP = 1.5×ATR (variants 0.75/1.5, 1.0/2.0);
compare vs current pivot logic on the same bias signal.
Prediction: current 1:1 SL-cap distorts geometry; ATR exits dominate.

## H9 — BE-lock audit  [QUEUED]
Rule: rerun best-so-far config with BE disabled, then BE at
{0.3, 0.5, 0.8}×ATR instead of fixed 0.72 JPY.
Prediction: unknown — measure whether BE saves more than it strangles.

## H10 — Day-of-week effect  [QUEUED]
Rule: slice best-so-far bias by weekday; drop any weekday only if
consistently negative across ≥7 years AND both half-samples.
Prediction: none (exploratory — extra strict acceptance).

## H11 — SMT divergence vs GBPUSD  [QUEUED, round 2]
Swings = 3-bar fractals on D1. Divergence: GBPJPY new 5-day high while
GBPUSD not (and mirror) → fade bias. Needs GBPUSD D1 fetch.
Prediction: weak/noisy; test last.

## H12 — Sizing: risk-% vs fixed lot vs DD-throttle  [QUEUED, after edge>0]
Run identical best-config decade with each sizing. Decision input, not
edge research. (User question — must answer explicitly.)
