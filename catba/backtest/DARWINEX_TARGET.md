# What a fundable DARWIN looks like — and where CatBa stands

Reference for building toward Darwinex capital allocation. (Darwinex's exact
attribute algorithm is proprietary and evolves — this is the substance +
directional targets, not their precise formula.)

## The mental model
Darwinex **normalizes every strategy to the same risk (VaR)** and then funds
whoever manages that risk **best and most consistently**. So they don't reward
high returns — they reward **risk managers**. The winning question isn't "how
much did you make?" but "how *reliably* did you make risk-adjusted returns,
across time, without blowing up, with room to scale?"

## The target profile (what scores well)
| Dimension | Fundable target | CatBa v1.1 | Gap |
|---|---|---|---|
| **Track record** | 12-24+ months REAL/forward, 100s of trades | 0 months forward (backtest only) | ❌ biggest gate |
| **Forward Sharpe** | > 1.0 sustained | 0.87 backtest -> ~0.4-0.7 fwd likely | ⚠️ borderline |
| **Consistency / durability** | steady months, returns spread across time | lumpy (2022/2024 carry it) | ❌ key weakness |
| **Max drawdown** | low & stable (single digits at their VaR) | ~11% at 0.5% — OK | ✅ decent |
| **Risk management (Ra)** | controlled VaR, adjusts exposure, no grid/martingale | fixed-fraction, clean | ✅ good |
| **Diversification / low mkt corr** | multiple uncorrelated instruments/signals | single instrument (GBPJPY) | ❌ concentrated |
| **Loss aversion / skew** | cut losses, let winners run (positive skew) | skew +0.51, PF 1.15 | ✅ good |
| **Capacity** | absorbs large capital w/o degrading | 1 trade/day, wide stops -> OK-ish | ✅ probably fine |
| **Divergence (execution)** | clean replication, low slippage impact | unknown until demo | ? |

## Where CatBa is genuinely strong
- Risk management + drawdown control (the sizing fix, ATR break-even, min-stop
  filter) — Darwinex rewards this.
- Positive skew / loss aversion — good.
- Clean, rule-based, no martingale — good.

## The three gaps that block funding
1. **No forward track record** — nothing counts until months of real trading.
2. **Durability (lumpy returns)** — carried by 2 trend years; Darwinex penalizes
   concentration in time. UNSOLVED (and 2-instrument diversification didn't fix
   it — the second edge was too weak).
3. **Single instrument** — concentration; low diversification score.

## What "fundable" would actually require (honest)
- A **forward Sharpe > 1 that HOLDS across many months** (not 2 lucky years).
- Returns **spread across time** — ideally from **2-4 genuinely uncorrelated
  edges** (different instruments AND/OR different signal logic), each with a
  REAL standalone edge (Sharpe meaningfully > 0). CatBa is one thin edge; you
  need a portfolio of them.
- 12+ months of clean forward execution.

## The honest path
1. **Now:** start a forward track record with CatBa v1.1 (cheap, learn the
   process, it's a plausible *first* DARWIN — not the one that pays big).
2. **In parallel:** develop a 2nd and 3rd *genuinely different* profitable edge
   (different market or logic, low correlation to GBPJPY continuation). This is
   a NEW research project, using the same discipline/harness we built.
3. **Combine** the real edges into a diversified, durable return stream — THAT
   is the profile that attracts meaningful allocation.

Bottom line: CatBa is a legitimate *first step* and a good learning vehicle, but
a fundable DARWIN needs **diversified, durable, forward-proven** risk-adjusted
returns — which means MORE real edges, not more tuning of this one.
