# CatBa research plan — prioritized experiment queue (2026-07-07)

Context: ~160+ trials deep. Validated filter stack so far: skip-Wednesday,
falling-knife, skip-December, ref-stop %-risk sizing, ema13, minStop30, cem12.
Two standing red flags: **phase-fragility** and **compounding-amplification** →
all headline % / DD numbers are optimistic; trust PF and IS/OOS robustness.
Overfitting risk is now HIGH — each new slice must clear: robust in BOTH halves
+ a mechanism, then tester-validate.

## TIER 1 — finish the config (do these, then stop tuning)
1. **Raise minStopPips (sweep 35/40/45/50).** SL-distance scan: tight stops
   (<46p) LOSE-both @41% win; wide win 68%. Current 30 is too low. Mechanism:
   tight pivot stop = compressed/choppy setup. HIGH confidence. [tester]
2. **Full-stack run at 0.5% risk.** The actually-deployable config — get the
   honest, non-aggressive number (DD ~4-5%, return realistic). [tester]
3. **Filter-interaction / redundancy check.** Do Wed+knife+Dec+minStop stack, or
   overlap (e.g. minStop already removes most falling-knife trades)? Confirm each
   still adds after the others. [tester, ablation]

## TIER 2 — setup-quality dimensions (capturable, mechanistic; medium value)
4. **Entry depth vs EMA (addPipsToEMA sweep).** How deep the pullback must go —
   shallow vs deep touches may differ in quality. [python->tester]
5. **Yesterday close-position in its range.** Did yesterday close at its high/low
   (momentum) vs mid (indecision)? Momentum closes may give cleaner bias. [python]
6. **Multi-day bias consistency.** Yesterday AND day-before same direction (2-3
   day trend) vs alternating — stronger continuation? [python]
7. **Partial-TP + trail the runner (clean).** Earlier trailing broke via stacking;
   test partial-close at pivot TP + trail remainder, WITH the position guard. [tester]
8. **beAtrMult (break-even timing) sweep.** 0.2/0.3/0.4/0.5 — how early to lock BE.
   Only H9 tested a couple; sweep it. [tester]

## TIER 3 — lower priority (likely diminishing / overfitting-prone)
9.  Entry position vs pivots (PP/R1/S1 zones).
10. Overnight/weekend gap at entry.
11. Time-based max-hold exit (close if not profitable after N hours).
12. ADX-rising (slope) vs ADX-level (level gate already failed).
13. Holiday-adjacent day skips (needs holiday calendar dates).

## TIER 4 — strategic (beyond tuning this edge)
14. **Forward demo** — the ONE thing that gives real information. Validates whether
    the edge survives live spread/slippage and whether phase-0 stays lucky.
    Everything above is optimization; this is proof. HIGHEST real value.
15. **Second uncorrelated edge on a DIFFERENT instrument** — the durability fix for
    Darwinex (CatBa is one thin edge). A new research project, same harness.

## Honest recommendation
Do **TIER 1** (3 quick validations to finalize + get the real 0.5% number), then
**STOP tuning and start TIER 4.1 (forward demo)**. TIER 2/3 are diminishing
returns — real edges get proven forward, not found by more backtest slicing.
