# GBPJPY edge map — what's real, what's a mirage (2026-07-06)

Exhaustive, cost-aware, walk-forward search for tradeable edges on GBPJPY.

## The one real edge
- **Trend continuation** (daily EMA-cross w/ ATR risk, ref-stop sizing, min-stop
  filter) = **CatBa**. Backtest Sharpe ~0.70–0.87, decade net positive, survives
  costs. This is the instrument's exploitable behavior.

## Everything else tested — DEAD
| Family | Best look | Why it failed |
|---|---|---|
| Consolidation/range filter | — | Losses diffuse (low-vol chop + failed trends), not in ranges; every variant cut return AND Sharpe; IS winners collapsed OOS |
| Volatility throttle | — | CatBa's edge IS the vol tail; throttling cuts the edge, raises maxDD |
| Mean-reversion (turtle-soup + z-fade) | corr −0.06 to CatBa | Loses standalone (Sharpe −0.48); carry-trend pair punishes fading |
| London-expansion breakout | gross Sharpe 0.59, OOS holds, corr −0.15 | **Erased by 2-pip spread → Sharpe 0.05**; only ~2.2p/day gross |
| Hour-of-day / Tokyo drift | Sharpe 3.58 (!) | **Rollover artifact**: −18.7k-pip midnight gap under the entry; untradeable spread/swap |

## Structural reasons GBPJPY is a one-edge instrument
1. **Carry/rate-differential drift** → it trends; reversion doesn't pay.
2. **Intraday microstructure** → session "edges" are too small to beat spread,
   or are rollover-candle artifacts.

## Consequences
- CatBa's **lumpiness (2022/2024 carry it) is structural** to a lone trend edge
  and **cannot be diversified away on GBPJPY** — no 2nd uncorrelated, cost-
  surviving edge exists here.
- A durable, fundable profile needs a **2nd edge on a DIFFERENT instrument**
  (different driver: e.g. an index, a metal, a non-JPY FX with different
  microstructure) — not more work on GBPJPY.

## Methodology lessons (why retail backtests lie)
- **Always net out spread+commission.** A 2-pip cost flipped a "Sharpe 0.59
  edge" to nothing.
- **Distrust any edge concentrated at the rollover candle** (00:00 server) —
  spreads blow out 15–30 pips there and swap is marked into price.
- **Walk-forward (IS/OOS) catches overfits** that in-sample Sharpe hides
  (several variants: great IS, negative OOS).
