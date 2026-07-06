# CatBa improvement — 4 levers tested (2026-07-06)

Baseline = ref13ms: ema13, minStop30, FIXED LOT 0.10, full decade, MT5 tester.
BASELINE: net +682,752 (42.7%), PF 1.16, maxDD 9.7%, 9/11 green, worstYr -1.18%, score 21.7.

## #1 EXIT — "let winners run" / trailing  → NO FREE WIN (+ found a real EA bug)
| Variant | net% | PF | maxDD | green | note |
|---|---|---|---|---|---|
| baseline (fixed pivot TP + BE) | 42.7 | 1.16 | 9.7% | 9/11 | — |
| LWR 3xATR, no guard | 177 | 1.63 | **43.8%** | 1/11 | PATHOLOGICAL — position stacking |
| LWR 3xATR, guarded | 62 | 7.70 | 30.8% | 1/11 | only **31 trades** — multi-year holds |
| trail + keep TP, 1xATR | 35.4 | 1.15 | **6.8%** | 9/11 | lower DD, 2020 -5.8k vs -18.9k; 2026 worse; -17% return |

- Removing the TP to "let winners run" **breaks the system**: trades become multi-year
  holds, frequency collapses. CatBa is a **short-hold daily system** (median 7h,
  ~50-100p pivot targets), NOT a position trend-follower — there is no long tail
  *inside* trades to capture. Its good trend years = more winning short trades.
- Found a genuine EA weakness: the daily guard has **no concurrent-position limit**
  (`isAlreadyPlaceATradeToday` only blocks a 2nd entry same-day). Safe today only
  because trades close fast. ADDED `CountOpenPositions()` guard (active when
  trailing) to prevent stacking.
- Trail-while-keeping-TP is a real **risk-reduction option**: maxDD 9.7%->6.8%,
  return/DD 4.4->5.2, tames 2020 — but costs ~17% return. A *choice* (lower-DD
  mode), not a strict upgrade. Shipped OFF by default (`useTrailing=false`).

## #2 RISK-SHAPING for D-Score  → MARGINAL, no lever
- Compounding only scales WEALTH (Darwinex VaR-normalizes level away) — no score change.
- Vol-targeting: Sharpe 0.70->0.74 & vol-of-vol 0.35->0.26 (better risk stability),
  BUT maxDD 6.7%->9.9% and worst month deeper. Mixed; not worth the complexity.
- Sizing is already clean (equity-proportional ref-stop). No real gain here.

## #3 ROBUSTNESS  → CONFIRMED (config is a plateau, not a spike)
| ema | net% | PF | maxDD | green | score |
|---|---|---|---|---|---|
| 12 | 39.5 | 1.15 | 8.6% | 9/11 | 19.8 |
| **13** | **42.7** | **1.16** | 9.7% | 9/11 | **21.7** |
| 14 | 38.0 | 1.15 | 8.8% | 8/11 | 11.4 |
- ema13 is a modest local peak; neighbors are profitable with similar PF/DD — no
  cliff. Config generalizes. (minStop=30 was validated separately in earlier WF work.)

## #4 COST / EXECUTION realism  → HYGIENE fix, low return impact
- No explicit `Spread=` in INIs: tester uses "current" spread (~2p GBPJPY, realistic
  but NOT rollover-aware). We saw earlier how much costs matter (a 2p spread flipped
  a 0.59-Sharpe session edge to zero).
- Entry-hour scan: hr0 (server midnight = rollover) has 109 trades / +140k that are
  **spread-fragile** (real rollover spread 15-30p, unmodeled). That backtest profit
  won't fully survive live.
- Recommend: set an explicit conservative spread for honest backtests; consider
  blocking rollover-hour entries before forward deployment.

## Bottom line
None of the 4 is a free profit boost — the EA is already well-tuned. Real value:
(1) fixed a latent no-concurrent-position weakness; (2) proved CatBa is short-hold
(don't try to "let it run"); (3) confirmed parameter robustness (safe to deploy);
(4) flagged rollover-hour cost fragility. Optional "lower-DD mode" (trail+TP)
exists if Darwinex risk score matters more than raw return.

## #5 (bonus) TIMING FILTER — skip Wednesday entries  → REAL, tester-confirmed ✅
User asked about day-of-week / week-of-month / entry-hour filters. Tested all
with IS/OOS discipline (timing_filters.py). Week-of-month: no signal. Entry-hour
band: no robust losing band. Hold-time <2h loses -452k but is an EXIT property
(not tradeable at entry — losers just stop out fast). Day-of-week: WEDNESDAY.
- Wednesday net -124,778 over decade; negative 9/11 years, CONSECUTIVELY 2018-26
  (4 IS + 5 OOS). Only 2016-17 positive. Mechanism: FOMC lands on Wednesdays;
  Fed became highly market-moving post-2018; GBPJPY rate-sensitive carry pair.
- TESTER (blockEntryDOW=3): net 42.7%->45.7% (+7%), PF 1.16->1.22, worstYr
  -1.18%->-0.95%, score 21.7->24.2, 8/11 years improved. maxDD 9.7->10.3%
  (marginally worse). Real-time validatable: 2018-21 all negative -> would have
  been flagged end-2021 -> held every year 2022-26.
- Caveats: tested 5 weekdays (multiple-testing), but 9 consecutive yrs +
  mechanism + tester confirmation >> chance. Opt-in: blockEntryDOW=3.
- REFINEMENT idea (untested): skip only FOMC Wednesdays (~8/yr) vs all (~50/yr)
  to keep benign Wednesdays — needs an FOMC calendar.
VERDICT: adopt for the forward demo (A/B vs baseline). Strongest lead since
min-stop.
