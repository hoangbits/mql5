# CatBa backtest harness

Headless Strategy Tester tooling for the CatBa EA (GBPJPY H1), Darwinex MT5.

## Key decisions
- **Deposit currency = JPY** (`Currency=JPY`, `Deposit=1600000` ≈ $10k): GBPJPY profit
  is JPY and margin is GBP→JPY via GBPJPY itself, so the tester needs **only GBPJPY
  history** (no USDJPY/GBPUSD sync). %-returns and risk-% lot sizes are identical to a
  USD account; convert final equity at current USDJPY for reporting.
- **Model=1** (1-min OHLC): right granularity for an EA that checks every 12 min and
  enters at market. Real ticks reserved for final validation only (~2019+ on Darwinex).
- **Results via `OnTester()`** in CatBa.mq5 → writes per-year P&L + robustness metrics
  to `Terminal\Common\Files\catba_results.csv`. The HTML `Report=` directive silently
  writes nothing on build 5836 — don't rely on it.
- Custom optimizer score: `netPct * fracPositiveYears − 3·|worstYear%| − maxDD%`
  (−1000 if <30 trades) — hunts consistency, not just max profit.

## Files
- `grind.sh` — widening-window runs (2024→2016) to work around the tester's ~8-min
  M1-download timeout vs Darwinex's slow feed; each pass extends the local cache.
  Results land in `results/from_<year>.csv`.
- `grind_*.ini`, `baseline_full_jpy.ini`, `verify*.ini` — tester configs
  (`terminal64.exe /config:<ini>`).
- `parse_report.py` — parses MT5 HTML reports (when they exist) into per-year P&L.
- `catba_bt.py` — fast approximate Python port of the strategy for idea-screening
  (tester remains the source of truth).

## Workflow
1. Edit `catba/CatBa.mq5` (repo) → copy to terminal's
   `MQL5\Experts\Advisors\catba\` → compile with `MetaEditor64.exe /compile:...`.
2. Close the running terminal, run `terminal64.exe /config:<ini>` (ShutdownTerminal=1).
3. Read `Common\Files\catba_results.csv`.

## Baseline findings (2026-07-04)
- Lot-size bug fixed in `2bf4b1a` (was sizing ~16× too small; 0.2% risk → 0.00 lots
  → orders rejected, EA barely traded).
- With correct 2% sizing, 2025-06→2026-07: **−37.9%**, PF 0.76, maxDD 54% —
  the current parameters/logic have a negative edge at proper size; optimization
  and logic changes are required, not just tuning.
