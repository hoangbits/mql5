"""S1 screens for the two remaining ICT daily-bias signals.

H15 — Weekly-open premium/discount (pre-registered):
  weekOpen = open of the first D1 bar of the ISO week. At day i, using
  yesterday's close vs weekOpen: close > weekOpen = PREMIUM, close < = DISCOUNT.
  ICT primary: premium -> SELL bias (draw back to discount); discount -> BUY.
  Also report the CONTINUATION variant (premium->BUY) for contrast.

H11 — SMT divergence vs GBPUSD (pre-registered):
  GBPJPY makes a new 5-day high while GBPUSD does NOT -> bearish SMT -> SELL
  bias next day; mirror for lows -> BUY. (Fade the unconfirmed extreme.)

Metric: next day open->close in bias direction (pips of 0.01), per year.
Note: premium/discount and SMT are REVERSAL-flavored -> D1 close-to-close
is a FIRST-PASS filter only (see RESEARCH.md rule 7), not a final verdict.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"

def load(sym):
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 2000)
    return [(datetime.fromtimestamp(int(x['time']), tz=timezone.utc),
             float(x['open']), float(x['high']), float(x['low']), float(x['close']))
            for x in r] if r is not None else []

def show(name, rows):
    by = defaultdict(lambda: [0, 0, 0.0])
    for y, h, m in rows:
        s = by[y]; s[0] += 1; s[1] += h; s[2] += m
    print(f"--- {name} ---")
    print(f"{'Year':>6} {'Days':>6} {'Win%':>7} {'Avg(pips)':>10}")
    tn = th = 0; tm = 0.0; neg = []
    for y in sorted(by):
        n, h, m = by[y]
        avg = m / n / 0.01
        if avg < 0: neg.append(y)
        tn += n; th += h; tm += m
        print(f"{y:>6} {n:>6} {100*h/n:>6.1f}% {avg:>9.1f}")
    if tn:
        print(f"{'ALL':>6} {tn:>6} {100*th/tn:>6.1f}% {tm/tn/0.01:>9.1f}   neg={neg}")
    print()

def main():
    assert mt5.initialize(path=PATH), mt5.last_error()
    mt5.symbol_select("GBPJPY", True); mt5.symbol_select("GBPUSD", True)
    gj = load("GBPJPY"); gu = load("GBPUSD")
    mt5.shutdown()
    print(f"GBPJPY {len(gj)} bars, GBPUSD {len(gu)} bars\n")

    # ---- H15 weekly-open premium/discount ----
    week_open = None; prev_week = None
    prem_ict = []; prem_cont = []
    for i in range(1, len(gj)):
        t, o, h, l, c = gj[i]
        iso = t.isocalendar()[:2]
        if iso != prev_week:
            week_open = o; prev_week = iso   # first bar of the week
        pc = gj[i-1][4]                       # yesterday's close (known at day start)
        if pc == week_open: continue
        premium = pc > week_open
        today = c - o
        # ICT: premium -> sell
        bias_ict = -1 if premium else 1
        prem_ict.append((t.year, 1 if bias_ict*today > 0 else 0, bias_ict*today))
        prem_cont.append((t.year, 1 if -bias_ict*today > 0 else 0, -bias_ict*today))
    show("H15 weekly premium/discount — ICT (premium->SELL)", prem_ict)
    show("H15 weekly premium/discount — CONTINUATION (premium->BUY)", prem_cont)

    # ---- H11 SMT vs GBPUSD ----
    # align by date
    gu_by = {b[0].date(): b for b in gu}
    smt = []
    for i in range(5, len(gj)-1):
        t = gj[i][0].date()
        if t not in gu_by: continue
        # 5-day high/low on each (bars i-5..i)
        gj_win = gj[i-5:i+1];
        # build GBPUSD window aligned by same dates
        dates = [b[0].date() for b in gj_win]
        gu_win = [gu_by[d] for d in dates if d in gu_by]
        if len(gu_win) < 5: continue
        gj_newhigh = gj[i][2] >= max(b[2] for b in gj_win[:-1]) and gj[i][2] == max(b[2] for b in gj_win)
        gj_newlow  = gj[i][3] <= min(b[3] for b in gj_win[:-1]) and gj[i][3] == min(b[3] for b in gj_win)
        gu_newhigh = gu_win[-1][2] == max(b[2] for b in gu_win)
        gu_newlow  = gu_win[-1][3] == min(b[3] for b in gu_win)
        bias = 0
        if gj_newhigh and not gu_newhigh: bias = -1   # bearish divergence -> sell
        elif gj_newlow and not gu_newlow: bias = 1    # bullish divergence -> buy
        if bias == 0: continue
        nt = gj[i+1]                                   # next day
        today = nt[4] - nt[1]
        smt.append((nt[0].year, 1 if bias*today > 0 else 0, bias*today))
    show("H11 SMT divergence vs GBPUSD (fade unconfirmed extreme)", smt)

if __name__ == "__main__":
    main()
