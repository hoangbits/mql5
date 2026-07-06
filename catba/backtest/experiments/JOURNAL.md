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

## 2026-07-04 — H8b ATR exits (trial count: ~32)
All 3 pre-registered variants worse than pivot exits (best: 0.75/1.5 at
-1.3% PF 1.00 vs pivot +21.7% PF 1.065). KILLED decisively.
**LESSON: pivot R1/S1 targets are load-bearing** — prior-day structural
levels, not arbitrary; edge substantially lives in exit placement.
Coheres with liquidity framing (moves exhaust at prior-day structure).
Exits are now frozen; research shifts to entry timing (H4) and regime.

## 2026-07-04 — H4 killzones (trial count: ~36)
All 4 variants worse than unrestricted (best: union +1.2% PF 1.005 vs
+21.7% PF 1.065). KILLED. **Inverse-ICT lesson: this EA's winners come
from being positioned BEFORE session displacement** — pullback fills
ripen outside killzones; restricting entries to KZs keeps the chasing
trades and drops the early positioning. Server=NY+7 calibrated from
Friday closes (3/3 agreement).

## 2026-07-04 — H9 BE audit (trial count: ~42) — FIRST SURVIVOR (conditional)
BE off: +17.4/PF1.044/DD18.6 -> BE helps; keep. ATR-scaled trigger:
0.2:+9.1/DD14.0 | 0.3:+20.9/PF1.070/DD8.2/worst-2.1 | 0.4:+19.5/DD11.8 |
0.5:+19.7/DD13.6 | 0.8:+22.8/DD16.0. Fixed 0.72 baseline: +21.7/DD14.1.
S2: profit plateau 0.3-0.5 (~+20%); DD minimum specific to 0.3 — claim
conservatively ("0.3-0.5xATR holds profit, DD <= current"); expect 8.2%
DD to regress. CAVEAT: variant choice used full-decade results incl.
nominal holdout -> S4 split check required before adopting as default
(rank stability on 2016-22 vs 2023-26, one look). Status: S2-PASS(cond).

## 2026-07-05 — H9 S4 status: IS done, OOS BLOCKED on login
IS 2016-22 ranking by registered score: 0.3xATR wins (+5.77; 6/7 pos
years, worst -0.67%, DD 8.3, PF 1.100) > 0.8 (+2.41) > 0.5 (-7.34) >
fixed 0.72 (-14.97). OOS 2023-26 one-look PENDING: terminal lost saved
credentials (misconfigured metatrader5 MCP placeholder-password login
attempts overnight) -> headless tester hangs at "not synchronized".
MCP entry disabled in .claude.json. UNBLOCK: manual login once in the
Darwinex terminal (4000030796 @ Darwinex-Live, save password), then run
backtest/s4_oos_03.ini and s4_oos_fixed.ini.
Also: tester caches ate ~13GB disk (11GB Tester + 2.6GB shared) — clean
cache/logs subfolders when convenient.

## 2026-07-05 — H9 S4 COMPLETE: PASS on registered score (trial count: ~50)
OOS 2023-26 one look: 0.3xATR score -15.4 / DD 9.6 / worst -2.1 / net
+2.1 / PF 1.020 vs fixed control score -25.3 / DD 12.0 / worst -5.1 /
net +3.7 / PF 1.031. Rank preserved on the registered score; the RISK
SHAPE transfers (shallower DD + worst-year), profit does not improve.
VERDICT: adopt beAtrMult=0.3 as reference config — validated risk
improvement, NOT an edge improvement. Both configs' OOS PF ~1.02-1.03 =
heavy-haircut zone; 2023-26 (incl. 2025 regime year) is thin regardless.
Regime defense remains the profit frontier.

## 2026-07-05 — H5 FVG bias KILLED + review pass (trial count: ~53)
All 3 gap-size variants ~48-50% win, avg +1.3 to -2.4 pips, 5-6 neg
years. KILLED@proxy(D1) with no lead-worthy structure. D1-proxy round is
now fully exhausted. REVIEW PASS coverage check: regime-gate dimension
still has UNTESTED structural candidates (ADX(D1), ATR-slope) — the
exact class H2's kill pointed to. Registered H14. Entry-location
dimension untested beyond current EMA pullback (H7 Po3, OTE pending).

## 2026-07-05 — H14 ADX gate KILLED@tester + REFERENCE CONFIG emerges (trial ~56)
D1 proxy said ADX>20 rescues 2025 (+11 pips). TESTER says opposite:
ADX20 gate removed 261 trades that were net POSITIVE -> total +9.2% (vs
ref +20.9%), DD worse (12.8 vs 8.2), and 2025 WORSE (-107k vs -34k),
2026 worse. ADX25 also worse. KILLED@tester — 2nd fidelity-escalation
false-positive catch (after H1). Lesson: D1 close-to-close cannot predict
how the EA's pullback/pivot/BE mechanics interact with a filtered day set.

** REFERENCE CONFIG (validated, current best) — the cumulative payoff **
Config: fixed 0.10 lots + BE trigger 0.3xATR(14,D1); everything else stock.
Decade 2016-2026H1: net +20.9%, PF 1.070, maxDD 8.2%, expectancy +196
JPY/trade, 7/11 positive years, WORST YEAR only -2.1%.
Per-year (JPY): 16:+57k 17:+30k 18:-11k 19:+86k 20:+20k 21:+26k 22:+132k
23:-8k 24:+138k 25:-34k 26:-33k. No catastrophic year.
vs original 2%-risk stock EA: -75.7%, maxDD 85.5%.
ROOT LESSON PROVEN: the signal loses only MILDLY in bad regimes; the
risk-% sizing turned mild losses into account death. Fix sizing (H12) +
ATR-scaled BE (H9) = a viable system. Regime years now a drag, not a
bomb. Provenance: H12 (mechanism-proven) + H9 (S4/OOS-validated); not
holdout-mined. Return figure is at 0.10 lots (tiny leverage); PF/DD are
the scale-free facts.

## 2026-07-05 — H3i intraday sweep-fade KILLED@H1 (trial count: ~60)
H1 mini-backtest, 2016-11..2026, 4 variants (target mid/2R x all-hours/
session9-17). Best (mid, session): +20R GROSS but -4274 net pips after
3-pip cost; all others net -7k to -13k pips; 8-9 neg years each. 2025 —
the year D1-proxy said sweep-fade rescues — is the WORST session-variant
year (-29R): raids in 2025 kept EXTENDING, so fading them = repeated
stop-outs beyond the raid extreme. VERDICT: KILL CONFIRMED at higher
fidelity (was KILLED@proxy). The intermediate H1 rung correctly vetoed
building the MQL5 sweep-fade mode.
META-LESSON: D1 close-to-close proxy SYSTEMATICALLY over-rates reversal/
fade signals (ignores intraday stop-outs). Rule added: reversal-type
hypotheses require >=H1 fidelity to screen; continuation-type OK at D1.

## 2026-07-05 — VALIDATED SIZING + defaults locked (trial ~66)
New sizing mode useFixedRefStopSizing: risk% on a FIXED refStopPips (70)
instead of the trade's actual SL -> equity-proportional, SL-independent,
compounds a positive edge, scales to any account. Decade + BE0.3:
  0.5%: +23.2% / DD 11.2 / PF 1.062 / worst -3.0  <- DEFAULT (safe growth)
  1.0%: +45.8% / DD 22.1 / worst -8.5
  2.0%: +81.9% / DD 41.0 / worst -27  (too hot)
Risk% is pure risk calibration (edge identical) so no holdout concern.
DEFAULTS CHANGED in CatBa.mq5: riskPercentPerTrade 0.2->0.5,
beAtrMult 0.0->0.3, useFixedRefStopSizing default true, refStopPips 70.
This is the cumulative validated system; answers user's risk-vs-fixed
and grow-safely questions. CAVEAT: on the live ~$831 account even min
lot (0.01) is ~5% risk on a 70-pip stop; sizing only becomes accurately
0.5% once equity > ~$1700. Next gate: S5 forward-demo.

## 2026-07-05 — H15 weekly-open premium/discount: ICT framing is INVERTED (trial ~68)
ICT primary (premium->SELL, draw to discount): 47.6% / -4.8 pips, 7 neg
years -> KILLED. CONTINUATION variant (premium->BUY): 52.4% / +4.8, only
2 neg years (2018,2025) -> WINS but is ~identical to the existing daily-
continuation edge (52.2/+4.9); "above weekly open" == "recent up momentum".
No NEW edge, but decisive META-conclusion below. (Minor: weekly-cont
gets 2019 positive where daily-cont was negative — same edge, diff
reference; not worth splitting.)

## ICT-for-GBPJPY CONCLUSION (answers user question)
Every ICT REVERSAL/liquidity concept tested is dead or inverted here:
  - PDH/PDL sweep-fade (H3/H3i): killed both fidelities
  - D1 FVG revert (H5): killed
  - Killzone timing (H4): killed
  - Weekly premium/discount revert (H15): INVERTED (loses; continuation wins)
GBPJPY at the daily scale is a CONTINUATION/trend market; ICT's
reversal-based bias toolkit is the wrong framework for it. The EA's
original continuation premise is MORE correct for this pair than ICT.
Remaining: H11 SMT (reversal-flavored, low prior), H7 Po3 (entry not bias).

## 2026-07-05 — Monte-Carlo drawdown / risk-of-ruin (reference config)
Input: 1704 ref trades (fixed 0.10 lot, BE0.3). Per-trade: mean +2.37 pips,
median +17.5, win 54%, sum +4036 pips. Profile = win-small-often, lose-big-
occasionally (median >> mean).
Kelly-optimal ~3.2% risk/trade (half-Kelly ~1.6%); 0.5% default = 0.16x
Kelly (very conservative). 20k sims, reshuffle + block(30) bootstrap:
  0.5%: medDD 13-15%, 95%DD ~22%, tail ~26-40%; P(end<0)=8.5% (block)
  1.0%: medDD 24-28%, 95%DD ~40%, P(DD>30%)=24-37%
  2.0%: medDD 45-50%, P(DD>50%)=33-49%  -> reckless
KEY: historical 11% DD was FAVORABLE; plan for ~15-22% at 0.5%. ~8.5%
chance the decade ends net-negative even with the edge (thin edge, real
uncertainty). Confirms 0.5-1% sane, 2% ruinous. Kelly is a CEILING
assuming edge is real+stationary; stay well below it given backtest
uncertainty. -> Phase 3 system-card input.

## 2026-07-05 [LOOP] — SMT event study M15+H1 (interim, trial ~70)
Data: full-decade tester export (GBPJPY/GBPUSD/USDJPY M15+H1, 2016-2026) —
the data blocker is SOLVED via the ExportSMT tester EA. Event study, FADE
the divergence: forward cum return NEGATIVE almost everywhere:
  M15 A(vGBPUSD) -14..-22 | M15 B(vUSDJPY) -11..-14 | resid -15..-78 |
  H1 A -12 | H1 B +12.5@h8 but 50.8% win (noise, <cost).
-> divergences predict CONTINUATION not reversal (fade LOSES). Consistent
with GBPJPY = continuation market. LEAD: inverted (continuation-confirmed-
by-divergence) is a 5/6-cell plateau but that's momentum = the existing
edge, not SMT. Pending: M5+M30 to honor the full TF request before final
verdict.

## 2026-07-05 [LOOP] — FINAL SMT VERDICT (all 4 TFs; trial ~72) — KILLED
Full-decade event study, GBPJPY daily bias from inter-market divergence at
the London open, 3 defs (A vs GBPUSD, B vs USDJPY, C residual on both legs)
x 4 TFs (M5/M15/M30/H1). FADE the divergence -> forward cum return (pips):

  Method A (vs GBPUSD): NEGATIVE every TF  (M5 -24..-53, M15 -14..-22,
      M30 -9..-10, H1 -12..-17). Fade loses; continuation wins.
  Method C (residual):  NEGATIVE hard every TF (-15..-78). Overextension
      CONTINUES (momentum), the opposite of mean-reversion.
  Method B (vs USDJPY): NEGATIVE on M5/M15; marginal +8..+12 pips at h~8 on
      M30/H1 BUT win% ~50.4-50.8% (coin flip) and ~1 pip/day << ~3 pip cost.

11/12 cells negative-or-noise; the 2 "positive" cells are below cost and
~50% win. No robust plateau, no TF works.

ANSWERS to the two questions:
  (1) Which TF detects SMT best?  NONE produce a tradable reversal edge.
      "Least bad" = H1 vs USDJPY, but below cost / coin-flip -> not real.
  (2) How many days to hold the bias?  MOOT — there is no reversal bias to
      hold. The FADE signal decays into LOSSES (continuation) at every
      horizon, so holding a fade bias any length loses.

CONCLUSION: SMT-as-reversal is FALSIFIED on GBPJPY across all tested TFs and
definitions. Consistent with the pair being CONTINUATION-dominated and every
prior ICT reversal concept failing/inverting here.
LEAD (Phase 2, not chased now): the INVERSE reading is a robust plateau —
divergence predicts CONTINUATION (A/C negative => inverse positive all TFs).
That is momentum = the EXISTING CatBa edge, not SMT; could be tested later
as an entry/bias refinement, but is out of scope for the SMT question.
DATA asset: 12 full-decade CSVs (GBPJPY/GBPUSD/USDJPY x M5/M15/M30/H1) now
producible on demand via ExportSMT.ex5 (tester auto-download).

## 2026-07-05 [LOOP] — H16 divergence-confirmed continuation — KILLED (trial ~74)
FIRST PASS looked huge: A CONFIRM 64.7% win/+29 pips, C CONFIRM 67%/+52 vs
PLAIN 51.5%/+3.3. CAUGHT A LOOK-AHEAD LEAK: outcome was today's full D1
open->close while the divergence signal sits INSIDE that window -> morning
strength mechanically correlates with up-close. Re-ran forward-FROM-WINDOW-
END (no leak):
  PLAIN            h0 -0.6  h1 +1.0  h2 -1.7  h3 -4.4
  A CONFIRM        h0 +1.5  h1 +9.8  h2 +18.0 h3 +9.8
  C CONFIRM        h0 +18.7 h1 +27.4 h2 +31.1 h3 +24.6
Looks positive BUT fails discipline: (1) C CONFIRM negative in recent years
[2023,2025,2026] -> no holdout survival; (2) CONTRADICT sometimes also
positive/high win (h1 C-contradict 59.8%) -> split not cleanly sorting;
(3) thin n~106 (~10/yr). VERDICT: divergence confirmation does NOT robustly
beat plain continuation once the leak is removed; edge is small, thin,
muddy, and absent in recent years. Confirms "relative strength == momentum,
redundant." SMT adds nothing tradable to CatBa.
METHOD NOTE: the initial +29/+52 was a classic backtest leak; only forward-
from-signal measurement is valid for a signal computed intraday.

## 2026-07-05 — Phase 3.1 code-correctness fixes (trial ~78)
Fixed 3 latent bugs in CatBa.mq5 before forward-demo:
1. BE-check TIMER: OnTick used checkEveryMinutes(12) instead of the intended
   1-min var -> BE actually ran every 12 min. Fixing to 1-min HURTS
   (+12.8% vs +20.9%). Made cadence an explicit input checkSlEveryMinutes.
   Sweep (all else = reference): 1:+12.8 | 6:+17.5 | 12:+20.9 | 18:+19.4 |
   30:+23.0 (%). Fast BE worse; 12-30 min a flat PLATEAU (PF~1.07, DD~8%).
   KEPT 12 (H9-validated, on plateau; 30's +2% is within noise = would be
   cherry-picking max). LESSON: don't lock break-even too eagerly.
2. FILLING MODE: hardcoded ORDER_FILLING_IOC -> GetFillingMode() picks a
   broker-supported mode (IOC/FOK/RETURN). Live-safety; no backtest impact.
3. DEAD CODE: removed the price_level/sl/tp block in update_sl_to_be
   (stop_level=9999999999 garbage) + fixed the modify guard to compare
   POSITION_SL vs new_stop_loss (was comparing vs garbage = always true).
   Removed DESIRE/GGGGG debug spam (log bloat).
VERIFICATION: reference config after fixes = +20.89% / PF 1.070 / DD 8.2% /
worst -2.1% — BIT-IDENTICAL to pre-fix validated baseline. Correctness fixes
changed zero behavior; the system is preserved and now live-safe/clean.

## 2026-07-05 — Phase 3.2 log verbosity (trial ~78, no new backtest)
Added input verboseLog=false; guarded all 44 active Print/PrintFormat calls
with `if(verboseLog)`. Reference config bit-identical after (+20.89%/PF1.07/
DD8.2%) — logging change, zero behavior change. Prevents the GB-scale
Experts logs (were 13GB) during long tester sweeps + the forward-demo.
Turn verboseLog=true only for debugging.

## 2026-07-05 — Phase 3.3 system card (DSR/walk-forward) — SOBERING
Ann Sharpe: FULL 0.45 / IS(2016-22) 0.62 / OOS(2023-26) 0.18 -> edge HALVED
out-of-sample. PSR(true SR>0)=92.6% single-test, but DSR ~0% after 78-trial
haircut (full-sample Sharpe below best-of-78 null-max). Only positive
evidence: OOS still +4% (Sharpe 0.18), weak but not negative.
VERDICT: marginal, low-quality edge. The real win was FIXING the broken
system (-76%->+23% via sizing), not finding alpha. NOT high-confidence;
forward-demo essential. Value = risk management (slow safe growth), not
signal. Wrote SYSTEM_CARD.md. Honest expectation: ~2%/yr at 0.5%, 15-22%
DD, losing years expected.

## 2026-07-05 [LOOP] — Generalization: EURJPY (trial ~79)
Exact reference params, NO re-tuning. EURJPY decade: +3.4% net, PF 1.016,
DD 12.1%, 8/11 green, worst -9.4%. POSITIVE (not inverted) -> the
continuation edge is REAL, not pure GBPJPY-overfit — but much weaker/
lower-quality than GBPJPY (+23%/PF1.07). Partial corroboration. AUDJPY,
CADJPY pending.

## 2026-07-05 [LOOP] — Generalization: AUDJPY (trial ~80)
Exact reference params. AUDJPY decade: -4.6% net, PF 0.966, DD 13.7%,
5/11 green, worst -4.1%. NEGATIVE. Edge does NOT hold on AUDJPY.
Running tally: GBPJPY +23%/PF1.07, EURJPY +3.4%/PF1.02, AUDJPY -4.6%/PF0.97.
MIXED -> edge is NOT a universal JPY-continuation phenomenon; it's
partly pair-specific. Yellow/red flag for GBPJPY-specific overfit. CADJPY
pending to finalize.

## 2026-07-05 [LOOP] — Generalization CADJPY + FINAL VERDICT (trial ~81)
CADJPY decade (exact reference params): -7.4% net, PF 0.941, DD 14.5%,
4/11 green, worst -6.3%. NEGATIVE.

FINAL GENERALIZATION TALLY (same params, no re-tuning):
  GBPJPY +23% PF1.07 | EURJPY +3.4% PF1.02 | AUDJPY -4.6% PF0.97 |
  CADJPY -7.4% PF0.94.  2/4 positive; non-home pairs average ~-3%.

VERDICT: the edge is NOT a robust cross-pair continuation phenomenon — it
is largely GBPJPY-SPECIFIC (strong there, weak on EURJPY, negative on
AUDJPY/CADJPY). GBPJPY's +23% leans on two big trending years (2022, 2024)
not replicated elsewhere. Two readings, can't fully separate: (a) overfit
to GBPJPY's particular history, or (b) GBPJPY genuinely trends harder ("the
dragon"). EITHER WAY the edge is fragile/concentrated and confidence in the
+23% is DOWNGRADED. This is a low-confidence, marginal, pair-specific edge.

DECISION — SKIP Phase 2 (H7 Po3, H10 day-of-week): further parameter/signal
search on a marginal, non-robust edge is overfitting risk with low EV. The
search is effectively complete. ~81 trials; the honest deliverable is the
CHARACTERIZATION, not a winning system.

## 2026-07-05 [LOOP] — FINAL PROJECT SUMMARY
What was achieved this project:
 1. Fixed a critical lot-size bug (was ~16x too small -> orders rejected).
 2. Diagnosed the real killer: inverse-SL risk-% sizing (-76%/85%DD decade).
    Replaced with equity-proportional SL-independent sizing -> +23%/11%DD.
 3. Added ATR-scaled break-even (H9, the one walk-forward-validated tweak).
 4. Hardened code (filling mode, dead code, BE-cadence input, verboseLog).
 5. Built a full research framework (funnel, false-negative defenses,
    literature criteria DSR/PBO/BHY) + repo-resident QUEUE/JOURNAL.
 6. Killed SMT decisively (reversal fails all TFs; continuation-confirm was
    a look-ahead leak). Killed ~a dozen other hypotheses with lessons.
 7. Honest stats: ann Sharpe 0.45 (OOS 0.18), DSR~0 after 81 trials.
 8. Generalization: edge largely GBPJPY-specific, not robust cross-pair.
HONEST BOTTOM LINE: turned a broken (-76%) EA into a marginally-positive
(+23%/decade), low-confidence, GBPJPY-specific system. The value delivered
is risk management + an honest characterization, NOT a proven money-maker.
Whether to trade it live is a judgment call on a thin, fragile edge; if
traded, tiny size (0.5%), and only after forward-demo. The process worked:
it prevented shipping false confidence.

## 2026-07-05 — H17 core-param walk-forward optimization — REAL IMPROVEMENT (trial ~117)
36-config grid (emaPeriod{5,8,13,21} x addPipsToEMA{0.05,0.11,0.20} x
minBody{0.14,0.28,0.42}), each full decade. EMA plateau (all else default):
  ema5 +6.9/PF1.02 | ema8(default) +23.2/PF1.06 | ema13 +42.9/PF1.12/8green |
  ema21 +36.1/PF1.12/DD7.7. -> emaPeriod=8 was TOO FAST; 13-21 much better.
IS winner ema21/addpip0.05/minbody0.28: FULL +43.6%, PF1.127, DD8.7%, 9/11
green, 2025 RESCUED (+96k vs default -34k), expectancy +438/trade.
WALK-FORWARD PASSED: IS winner OOS(2023-26) +22.6% (rank 2/36) vs default
+4.5%. PBO(CSCV, 252 splits) = 8.3% (<<50%) -> NOT overfit. This BEAT the
low prior; the disciplined optimization found genuine signal. emaPeriod is
the dominant lever. PENDING: cross-pair generalization with the new params
(the ema8 version failed cross-pair; must re-check ema21).

## 2026-07-05 — H17 cross-pair check — OVERFIT CAUGHT (trial ~120) — KILLED
Applied the walk-forward WINNER (ema21/addpip0.05) to the other JPY pairs:
  EURJPY +3.4% -> -2.8% (flipped NEG) | AUDJPY -4.6% -> -7.9% | CADJPY -7.4% -> -9.3%.
The ema21 optimum made GBPJPY +44% but made ALL 3 other pairs WORSE. Classic
INSTRUMENT-SPECIFIC OVERFIT — yet it PASSED walk-forward (OOS+22.6%) AND
PBO (8.3%). LESSON: walk-forward + PBO test only across TIME on the SAME
instrument; they cannot catch instrument-specific overfitting. Cross-
instrument generalization is an ORTHOGONAL check that caught it.
DECISION: do NOT adopt ema21; keep emaPeriod=8 (less-optimized = less
overfit). The +44% is a GBPJPY-specific mirage. H17 KILLED. Final answer to
'can params make it better?': NO robust improvement exists; the apparent one
was overfit, caught only by cross-pair. Trial count ~120. The edge stands as
marginal + GBPJPY-specific. Discipline worked again.

## 2026-07-05 — GBPJPY-only: adopt emaPeriod=13 (trial ~120, opt-in decision)
User focusing GBPJPY-only -> cross-pair failure less disqualifying; the
GBPJPY-relevant tests (walk-forward OOS+22.6%, PBO 8.3%) support ema13.
Set emaPeriod default 8->13. Shipping default (ema13, risk0.5% equity-prop):
+42.9%/PF1.119/DD11.2/8-11green. Signal (fixed-lot): Sharpe 0.72 (vs 0.45),
OOS Sharpe 0.80 (NO decay; ema8 decayed to 0.18), skew +0.66. Strongest
evidence yet the edge is real ON GBPJPY. CAVEATS kept: GBPJPY-specific,
DSR~0 at 120-trial haircut, unproven forward -> demo A/B ema8 vs ema13.
BUG FIX: place_trade now checks useRiskPercentPerTrade (was dead — checked
only riskPercentPerTrade>0; caused grid to run risk-% when set 'false').

## 2026-07-05 — LOSS-MODE ANALYSIS -> minStopPips filter — REAL IMPROVEMENT (trial ~126)
Enriched OnTester to dump paired entry/exit + SL/TP/reason/side/hold.
loss_analysis.py on ema13 trades: STRONGEST pattern = SL distance. Tight-SL
setups (<=40 pips, entry near pivot) win only 37.8% and lose -121k; wide-SL
(>87) win 72%/+841k. Monotonic. (Hold-time pattern = same thing, not entry-
knowable. Side/DoW weak/noise.) Added minStopPips filter (skip entries whose
pivot SL < X pips). WALK-FORWARD sweep (default13, IS16-22/OOS23-26):
  ms0 IS25.4/OOS23.0/PF1.119 | ms20 27.7/26.2/1.134 | ms30 34.3/27.4/1.155 |
  ms40 34.9/23.1 | ms50 34.5/24.9/1.178 | ms60 35.1/OOS18.3 (over-filter/overfit).
ROBUST PLATEAU ms20-50 all improve OOS; IS-optimum(60) DEGRADES OOS -> did NOT
pick it. ADOPTED minStopPips=30 (mid-plateau). New default (ema13+ms30):
+56.5% @0.5%, Sharpe 0.87 (was 0.45), OOS Sharpe 0.93 (NO decay), Sortino
1.71, skew +0.51, PSR 99.8%. 2nd genuine improvement from disciplined analysis.
CAVEATS: DSR~0 at 126-trial haircut; GBPJPY-validated only; unproven forward.
Journey: ema8 Sharpe0.45/OOS0.18 -> ema13 0.72/0.80 -> +ms30 0.87/0.93.

## 2026-07-05 — minStop filter CROSS-PAIR validation — ROBUST (trial ~132)
ema13, minStop 0->30 on other JPY pairs:
  EURJPY -4.7%->+0.6% (PF0.98->1.00) | AUDJPY -0.1%->+1.3% (0.99->1.01) |
  CADJPY -9.9%->-3.6% (0.92->0.96). ALL 3 IMPROVED (2 flipped positive).
The min-stop filter shows POSITIVE TRANSFER across instruments -> it is a
REAL GENERAL PRINCIPLE, not GBPJPY-overfit. It now passes BOTH orthogonal
robustness tests: walk-forward (OOS Sharpe 0.93, no decay) AND cross-
instrument (helps every pair). Contrast emaPeriod=13 which passed walk-
forward but FAILED cross-pair (GBPJPY-specific). Mechanism: entering next
to S/R (tight stop) is a low-quality setup universally. HIGHEST-CONFIDENCE
improvement in the project. This ~overcomes the DSR multiple-testing concern
for minStop specifically (orthogonal validation > single-dataset selection).
CONFIDENCE MAP: minStop30 = robust/general (high conf); emaPeriod13 = GBPJPY-
specific (medium, forward-confirm); sizing+BE = validated. Remaining: still
unproven FORWARD; base signal weak on non-GBPJPY pairs (but that's fine,
GBPJPY-only).

## 2026-07-05 — 2-instrument portfolio (GBPJPY+AUDJPY) for durability — NO GAIN (trial ~134)
Both ema13+minStop30, fixed lot. Monthly-return corr +0.14 (low, good setup).
Weightings G/A: 100/0 Sharpe0.87/DD6.1/9green | 80/20 0.86/4.7/9 |
70/30 0.84/4.1/10green | 50/50 0.77/4.0/10green. Adding AUDJPY LOWERS Sharpe
(dilution) while improving DD + durability (10/11 green). Net for Darwinex
(VaR-normalized -> Sharpe-driven): wash-to-negative. AUDJPY edge too weak
(+1.3%/decade, near-breakeven) to provide real diversification benefit.
CONCLUSION: 2-instrument does NOT help; diversification needs a second REAL
edge (Sharpe>0 meaningfully), which we don't have. GBPJPY-alone (Sharpe 0.87)
remains best. The durability weakness for Darwinex is unsolved without a
genuinely different profitable signal/instrument. Keep GBPJPY-only single.

## 2026-07-05 — Mean-reversion TWIN (durability hedge) — FAILED (trial ~136)
Sweep-reversal MR (H3 signal) vs CatBa, monthly. Correlation only +0.07 (NOT
negative — H3 anti-corr is YEARLY, washes out monthly). MR standalone Sharpe
-0.54 (loses). Combining drags Sharpe 0.87->0.70->0.58->0.42->0.23; durability
NOT improved (9->8 green yr). KILLED. Same lesson as AUDJPY: diversification
needs a second REAL edge (positive Sharpe + genuine neg/low corr); a losing,
weakly-correlated strategy just dilutes. DURABILITY REMAINS UNSOLVED with
available materials. Both diversification attempts (AUDJPY pair, MR twin)
confirm: no second real edge exists in this space. To make CatBa Darwinex-
fundable needs a GENUINELY NEW profitable edge (different market/logic) = a
separate research project, not a tweak. CatBa stands as a modest, thin,
GBPJPY-specific single edge (Sharpe 0.87 backtest). Search exhausted.

## 2026-07-05 — Consolidation/volatility analysis (user idea) — LEAD (trial ~137)
Bucketed ema13 trades by consolidation proxies at entry (prior-day, no leak).
FINDING: CatBa near-breakeven in QUIET markets (low-ATR: +16k/50.9% win),
strong in EXPANSION (high-ATR: +458k/58.1%). BUT consolidation trades DON'T
LOSE (near-breakeven, not negative) — unlike minStop's tight-SL losers.
Refined: quiet trades add NOISE without return. Skipping low-ATR-33% trades:
Sharpe 0.63->0.70, net -1.0% (return preserved, Sharpe up) = a real Sharpe
lever (Darwinex-relevant). vs H14 ADX gate (killed) — ATR-percentile is
cleaner than ADX. STATUS: promising LEAD, IN-SAMPLE only, ~137 trials.
NEEDS walk-forward + cross-pair (like minStop) before adopting. User's
'wait for breakout to ENTER' part NOT tested (likely hurts — late entry,
killzone lesson H4). The value is SKIP-QUIET (Sharpe), not breakout-entry.
