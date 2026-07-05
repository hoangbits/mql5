"""H3i intermediate-fidelity screen: intraday PDH/PDL sweep-fade on H1.

A rung above the D1 close-to-close proxy that killed H3. Models the actual
intraday mechanics the proxy could not see: raid of prior-day extreme,
rejection back inside, fade entry, stop beyond the raid extreme, asymmetric
target. NOT the MT5 tester (no pullback/EMA/pivot machinery) — a go/no-go
gate before committing MQL5 implementation.

Pre-registered rules (QUEUE.md H3i):
  PDH/PDL/mid from prior UTC day's H1-aggregated range.
  Raid: intraday H1 high > PDH (or low < PDL).
  Rejection: a later H1 bar CLOSES back inside [PDL, PDH] after a raid.
  Entry: fade at that close (raid high -> SELL, raid low -> BUY). 1/day.
  Stop: beyond the running day extreme at entry + buf (buf=0.05 = 5 pips).
  Target variants: (a) prior-day midpoint; (b) 2R fixed.
  Session variants: all hours; London/NY only (server hours 9-17 = NY+7).
Metrics: per-year win%, avg R, total R, net pips (3-pip cost/trade).
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"
PIP = 0.01
BUF = 0.05           # 5-pip stop buffer beyond raid extreme
COST_PIPS = 3.0      # round-trip cost assumption at this fidelity

def load_h1():
    assert mt5.initialize(path=PATH), mt5.last_error()
    mt5.symbol_select("GBPJPY", True)
    r = mt5.copy_rates_from_pos("GBPJPY", mt5.TIMEFRAME_H1, 0, 60000)
    mt5.shutdown()
    bars = [(datetime.fromtimestamp(int(x['time']), tz=timezone.utc),
             float(x['open']), float(x['high']), float(x['low']), float(x['close']))
            for x in r]
    return bars

def group_days(bars):
    days = defaultdict(list)
    for b in bars:
        days[b[0].date()].append(b)
    return sorted(days.items())

def sim(days, target_mode, session_only):
    # target_mode: 'mid' or '2R'; session_only: restrict entries to server 9-17
    trades = []  # (year, R, net_pips)
    for di in range(1, len(days)):
        _, pbars = days[di-1]
        day, tbars = days[di]
        pdh = max(b[2] for b in pbars); pdl = min(b[3] for b in pbars)
        pmid = (pdh + pdl) / 2.0
        raided_hi = raided_lo = False
        day_hi = -1e9; day_lo = 1e9
        entered = False
        for k, b in enumerate(tbars):
            t, o, h, l, c = b
            day_hi = max(day_hi, h); day_lo = min(day_lo, l)
            if h > pdh: raided_hi = True
            if l < pdl: raided_lo = True
            if entered: continue
            if session_only and not (9 <= t.hour < 17):
                continue
            side = 0
            if raided_hi and c < pdh: side = -1     # sell fade
            elif raided_lo and c > pdl: side = 1    # buy fade
            if side == 0: continue
            entry = c
            if side == -1:
                stop = day_hi + BUF
                risk = stop - entry
                tp = pmid if target_mode == 'mid' else entry - 2*risk
            else:
                stop = day_lo - BUF
                risk = entry - stop
                tp = pmid if target_mode == 'mid' else entry + 2*risk
            if risk <= 0 or (side == -1 and tp >= entry) or (side == 1 and tp <= entry):
                continue
            # resolve on subsequent H1 bars (this bar's remainder ignored: enter at close)
            res = None
            for b2 in tbars[k+1:]:
                _, _, h2, l2, _ = b2
                if side == -1:
                    hit_sl = h2 >= stop; hit_tp = l2 <= tp
                else:
                    hit_sl = l2 <= stop; hit_tp = h2 >= tp
                if hit_sl and hit_tp: res = -1.0; break      # conservative: SL first
                if hit_sl: res = -1.0; break
                if hit_tp: res = (abs(tp-entry)/risk); break
            if res is None:  # close at end of day
                last_c = tbars[-1][4]
                res = (side*(last_c-entry))/risk
            net_pips = res*risk/PIP - COST_PIPS
            trades.append((day.year, res, net_pips))
            entered = True
    return trades

def report(name, trades):
    by = defaultdict(lambda: [0,0,0.0,0.0])  # n, wins, sumR, sumpips
    for y,R,p in trades:
        s=by[y]; s[0]+=1; s[1]+= (1 if R>0 else 0); s[2]+=R; s[3]+=p
    print(f"--- {name} ---")
    print(f"{'Year':>6} {'N':>5} {'Win%':>6} {'avgR':>6} {'totR':>7} {'netPips':>8}")
    tn=tw=0; tR=0.0; tp=0.0; neg=[]
    for y in sorted(by):
        n,w,sR,sp=by[y]
        if sp<0: neg.append(y)
        tn+=n; tw+=w; tR+=sR; tp+=sp
        print(f"{y:>6} {n:>5} {100*w/n:>5.1f}% {sR/n:>6.2f} {sR:>7.1f} {sp:>8.0f}")
    if tn:
        print(f"{'ALL':>6} {tn:>5} {100*tw/tn:>5.1f}% {tR/tn:>6.2f} {tR:>7.1f} {tp:>8.0f}  neg={neg}")
    print()

def main():
    bars = load_h1()
    days = group_days(bars)
    print(f"H1 days: {len(days)}  {days[0][0]} -> {days[-1][0]}\n")
    for sess in (False, True):
        tag = "session9-17" if sess else "all-hours"
        report(f"H3i target=mid  {tag}", sim(days, 'mid', sess))
        report(f"H3i target=2R   {tag}", sim(days, '2R', sess))

if __name__ == "__main__":
    main()
