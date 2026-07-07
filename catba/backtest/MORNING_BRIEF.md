# CatBa — morning brief (overnight work, 2026-07-08)

You slept; I finished the 5-hour plan's autonomous pieces. Summary + the one
decision you should make before deploying.

## 1. The honest edge (realistic spread)
Your GUI test showing **PF 1.17** was correct; my headless 1.27 was optimistic
(headless tester uses ~0.5-pip spread; real Darwinex GBPJPY spread ~3 pips).
Recomputed from the trades, the gap is 100% spread. **Real edge: PF ~1.15–1.17**
— genuine but thin. Live slippage shaves a touch more → plan for **~1.15**.

## 2. Filters re-validated at realistic 3-pip spread — they PASS
Every filter still lifts PF at real cost (and *more* at higher spread, since they
cut marginal trades spread would sink):
| config | PF @3p |
|---|---|
| base (no filters) | 1.05  ← edge nearly gone |
| +skip-Wed | 1.11 |
| +falling-knife | 1.20 |
| +all 3 (incl. Dec) | 1.23 (pip) / ~1.17 (money) |
**The filters are most of the edge at real cost — keep them all on.**

## 3. THE DECISION: risk % (Monte Carlo at realistic spread)
| Risk | Decade return | Median maxDD | 95th-pct DD | Worst DD |
|---|---|---|---|---|
| 0.5% | +58% (~4.5%/yr) | 9% | 14% | 25% |
| 1.0% | +143% (~8.7%/yr) | 18% | 27% | 40% |
| **2.0% (your pick)** | +421% (~16.6%/yr) | **34%** | **48%** | **66%** |

**2% risk means a *typical* 34% drawdown and up to ~48–66% in bad runs.** That is
account-threatening and very hard to hold through psychologically. My strong
recommendation: **start at 0.5% (9% typical DD) or at most 1%.** The edge is thin
— aggressive sizing on a thin edge is how thin edges blow up. You can always raise
risk later once forward results confirm the edge; you can't un-lose a 50% drawdown.

## 4. One hidden-cost warning (rollover)
The backtest *likes* midnight-rollover (hr0) entries (+9 pips/trade) — but that's
a mirage: real rollover spread is 15–30 pips, which the backtest can't see. Those
109 trades will underperform live. Consider `skipHours="0"` for live (it makes the
backtest look slightly worse but protects real returns).

## 5. What to do next (unchanged, now with honest numbers)
1. **Forward demo at 0.5% risk** — the only way to measure real spread+slippage.
   Preset staged: `catba_forward.set` (I set it to 2% at your request — change
   `riskPercentPerTrade` to 0.5 first, given #3 above).
2. **Do NOT scale real money** until the demo confirms PF holds near ~1.15 live.
3. **Durability = a 2nd uncorrelated edge on a different instrument** — a new
   project, only after the demo proves the process.

## Bottom line
CatBa is a **real but thin, cost-sensitive edge** (PF ~1.15–1.17). Validated
across IS/OOS, cross-spread, and Monte Carlo. It's a legitimate first system —
but **size it small (0.5%)** and **prove it forward** before it earns real risk.
Everything is committed to git.
