"""H11b — intraday multi-TF SMT to predict DAILY bias (proof-of-concept).

Faithful to how ICT uses SMT: a SESSION-timed divergence, not a daily-bar
one. At the London open, does GBPJPY make a new session extreme that its
correlated partner fails to confirm? That divergence -> the day's bias.

Pre-registered (one clean rule, minimal variants to bound trial count):
  Session window: server hours [9, 9+WIN) (WIN=3) = London open (server=NY+7).
  Within the window, per symbol compute running high/low. Divergence at the
  window's LAST bar:
    bearish SMT: GBPJPY window-high == its window max AND strictly above the
      window OPEN, while PARTNER's last-bar high is NOT its window max
      -> SELL bias.
    bullish SMT: mirror on lows -> BUY bias.
  Bias measured against the DAY's open->close (in pips).
  Timeframes tested: M5, M15, M30, H1. Partner: GBPUSD (GBP leg).
Data note: uses whatever history the terminal has (recent). Reports the
window covered; if a TF looks predictive, escalate with a full download.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"
WIN_HOURS = 3
SESSION_START = 9   # server hour (London open ~ NY 02:00 = server 09:00)
TFS = [("M5", mt5.TIMEFRAME_M5, 60000),
       ("M15", mt5.TIMEFRAME_M15, 40000),
       ("M30", mt5.TIMEFRAME_M30, 30000),
       ("H1", mt5.TIMEFRAME_H1, 20000)]

def pull(sym, tf, n):
    r = mt5.copy_rates_from_pos(sym, tf, 0, n)
    if r is None or len(r) == 0:
        return []
    return [(datetime.fromtimestamp(int(x['time']), tz=timezone.utc),
             float(x['open']), float(x['high']), float(x['low']), float(x['close']))
            for x in r]

def day_open_close(gj_h1_or_any_daily, day):
    pass  # handled inline

def run_tf(name, gj, gu):
    # index intraday bars by day
    gj_days = defaultdict(list); gu_days = defaultdict(list)
    for b in gj: gj_days[b[0].date()].append(b)
    for b in gu: gu_days[b[0].date()].append(b)
    rows = []  # (year, hit, move_pips_in_bias)
    for day, jb in sorted(gj_days.items()):
        ub = gu_days.get(day)
        if not ub: continue
        jw = [b for b in jb if SESSION_START <= b[0].hour < SESSION_START+WIN_HOURS]
        uw = [b for b in ub if SESSION_START <= b[0].hour < SESSION_START+WIN_HOURS]
        if len(jw) < 3 or len(uw) < 3: continue
        j_hi = max(b[2] for b in jw); j_lo = min(b[3] for b in jw); j_open = jw[0][1]
        u_hi = max(b[2] for b in uw); u_lo = min(b[3] for b in uw)
        j_last = jw[-1]; u_last = uw[-1]
        bias = 0
        # bearish: GJ high made at/after and is window max above open; GU last high not window max
        if j_hi > j_open and j_last[2] >= j_hi - 1e-9 and u_last[2] < u_hi - 1e-9:
            bias = -1
        elif j_lo < j_open and j_last[3] <= j_lo + 1e-9 and u_last[3] > u_lo + 1e-9:
            bias = 1
        if bias == 0: continue
        # day open->close (use full day's first open and last close from GBPJPY intraday)
        day_open = jb[0][1]; day_close = jb[-1][4]
        move = bias * (day_close - day_open)
        rows.append((day.year, 1 if move > 0 else 0, move))
    return rows

def show(name, rows, span):
    by = defaultdict(lambda: [0, 0, 0.0])
    for y, h, m in rows:
        s = by[y]; s[0]+=1; s[1]+=h; s[2]+=m
    print(f"--- {name}  (data {span}) ---")
    if not rows:
        print("  no signals / no data\n"); return
    print(f"{'Year':>6} {'N':>5} {'Win%':>7} {'Avg(pips)':>10}")
    tn=th=0; tm=0.0
    for y in sorted(by):
        n,h,m=by[y]; tn+=n; th+=h; tm+=m
        print(f"{y:>6} {n:>5} {100*h/n:>6.1f}% {m/n/0.01:>9.1f}")
    print(f"{'ALL':>6} {tn:>5} {100*th/tn:>6.1f}% {tm/tn/0.01:>9.1f}\n")

def main():
    assert mt5.initialize(path=PATH), mt5.last_error()
    mt5.symbol_select("GBPJPY", True); mt5.symbol_select("GBPUSD", True)
    for name, tf, n in TFS:
        gj = pull("GBPJPY", tf, n); gu = pull("GBPUSD", tf, n)
        if not gj or not gu:
            print(f"--- SMT {name}: MISSING DATA (GBPJPY={len(gj)} GBPUSD={len(gu)}) ---\n")
            continue
        span = f"{gj[0][0].date()}..{gj[-1][0].date()} / GU {gu[0][0].date()}..{gu[-1][0].date()}"
        rows = run_tf(name, gj, gu)
        show(f"SMT {name} London-open divergence", rows, span)
    mt5.shutdown()

if __name__ == "__main__":
    main()
