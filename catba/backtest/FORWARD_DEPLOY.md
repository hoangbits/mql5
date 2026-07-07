# CatBa forward-demo deployment — step-by-step

Goal: run CatBa live on a DEMO account to see if the backtest edge is real,
before risking money. Preset: `catba_forward.set` (validated defaults, 0.5% risk).

## One-time setup (you, in MT5 — ~5 min)
1. **Open a DEMO account** (not your live one yet): File → Open an Account →
   pick Darwinex demo (or any demo) → finish. This keeps real money safe.
2. Open a **GBPJPY** chart, set timeframe to **H1**.
3. **Enable AutoTrading**: the "Algo Trading" button in the toolbar must be green.
4. Drag **CatBa** from Navigator → Expert Advisors onto the GBPJPY H1 chart.
5. In the inputs dialog: click **Load** → choose **catba_forward.set** → OK.
   (Confirm: riskPercentPerTrade=0.5, blockEntryDOW=3, useFallingKnifeFilter=true.)
6. A smiley face top-right of the chart = EA is running. Leave the terminal on
   (VPS ideal, or a PC that stays awake — CatBa checks every 12 min).

## What to watch (first 2-3 months)
- **Does it trade ~1x/day** and skip Wednesdays? (sanity check it's working)
- **Real drawdown vs backtest** (~16% was at 2%; at 0.5% expect ~4-5% — but live
  is usually worse). If live DD blows past backtest, the edge is weaker than hoped.
- **Compare monthly** to the backtest years. Watch spread/slippage drag.

## Decision gates
- **After ~1 month of sane demo behavior** → optional: go TINY-live on Darwinex
  (~$831) to start a real track record. Keep risk 0.5%.
- **After 3-6 months forward** → if the edge holds, THEN consider raising risk or
  a Darwinex DARWIN. If it doesn't hold, you learned it cheaply (no real loss).

## Honest expectations (from research)
- Backtest headline numbers (+508% etc.) are OPTIMISTIC — phase-fragility +
  compounding-amplification mean forward will be lower. Judge by drawdown and
  consistency, not the headline %.
- 0.5% risk is deliberately conservative. Don't start at 2% on real money.
- One thing at a time: no second instrument/edge until CatBa has forward data.
