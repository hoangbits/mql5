# CatBa Forward-Demo Runbook (S5 gate)

The final gate before real money. Everything upstream is backtested; this
checks the things a backtest **cannot**: real spreads, slippage, fill
quality, swap, weekend gaps, and that the EA has no live-only bugs.

## Honest expectation first (read this)
- The edge is **thin** (decade PF ≈ 1.06, ~52% continuation win rate).
  At 0.5% risk the backtest is ~**+2%/year** with ~11% max drawdown.
  This is a small, slow, positive edge — not a money machine.
- Trade rate ≈ **1/day max, ~150/year**, so a 4-week demo produces only
  ~10–20 trades. **That is far too few to confirm the edge statistically.**
- Therefore the demo's real job is **execution fidelity + bug-catching**,
  not re-proving profit. Edge confirmation needs many months of live-forward
  data (track it, but don't judge profit on 4 weeks).

## Setup
1. Open a **Darwinex demo** account (same server family, similar spreads).
   Fund it near your intended live size so min-lot behaves the same.
2. Attach `CatBa` to a **GBPJPY H1** chart.
3. Load inputs from `best_config_reference.ini` (or accept the compiled
   defaults — they are already the validated config).
4. Enable **Algo Trading** (Ctrl+E, button green). Confirm "AutoTrading"
   is on and the EA smiley is 🙂 not ☹.
5. Leave the terminal running continuously (VPS ideal; the EA checks every
   12 min and manages break-even — a closed terminal stops management).

## Daily / weekly checks (log in a sheet)
For each trade the EA takes, record: date, side, entry, SL, TP, lots,
exit, P/L, and the `CalculateLotSize` journal line. Then verify:

- [ ] **Lot size correct.** On demo equity E, lots ≈ (E × 0.005) sized on
      70 pips. If equity < ~$1700 it will be min lot 0.01 (expected).
- [ ] **SL/TP placed** at pivot levels; order `retcode` = DONE (10009).
- [ ] **Break-even moves** once price runs ~0.3×ATR(D1) in favour.
- [ ] **Max one trade/day**, bias matches yesterday's D1 direction.
- [ ] **Fills near intended price** — note slippage; big/frequent slippage
      or requotes = the backtest's fill assumptions are optimistic.
- [ ] **Spread at entry** logged — if routinely ≫ backtest, edge erodes.

## Pre-registered PASS / FAIL (decide before you start; one verdict)
Run **4 weeks minimum**. Then:

- **PASS (proceed toward small live):** no execution bugs; lot sizing,
  SL, TP, BE all behaved; realized slippage/spread in line with backtest;
  equity curve not materially worse than a same-period backtest run.
- **INVESTIGATE:** any mechanical bug (wrong lots, missing SL, BE not
  firing, duplicate/missed trades) → fix, re-demo. Do NOT go live.
- **FAIL the fidelity check:** slippage/spread so large that per-trade
  edge (~+0.14% of equity) is eaten → the strategy is not viable at this
  broker/latency; stop.

## Cross-check (do once, at demo start)
Run a backtest over the **exact demo period** with the same config, then
compare trade-for-trade against the demo. Divergence in *which trades*
fire = data/timezone issue; divergence in *fills only* = the slippage
you're measuring. Config for this run: `best_config_reference.ini` with
FromDate/ToDate set to the demo window.

## If PASS → live sizing
- Start at **0.5%** (default). Only raise toward 1% after a live-forward
  quarter that holds up. Never 2% (41% backtest DD).
- Remember the sub-$1700 min-lot over-risk: keep balance in mind.
