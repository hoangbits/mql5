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
