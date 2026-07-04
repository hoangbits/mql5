"""S1 screen for H3: PDH/PDL sweep-reversal bias (ICT turtle soup).

Pre-registered (QUEUE.md):
  Signal day = yesterday (i-1); prior day = i-2.
  Sweep-high: high[i-1] > high[i-2] AND low[i-2] < close[i-1] < high[i-2]
  Sweep-low : low[i-1]  < low[i-2]  AND low[i-2] < close[i-1] < high[i-2]
  Both-swept (outside bar closing inside) -> skipped (ambiguous).
  Bias: sweep-high -> SELL today; sweep-low -> BUY today.
  Variant a: trade only sweep days.  Variant b: non-sweep days fall back
  to continuation bias.  No other variants.
Metric: today open->close move in bias direction (pips), per year.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"

def load_d1():
    assert mt5.initialize(path=PATH), mt5.last_error()
    mt5.symbol_select("GBPJPY", True)
    r = mt5.copy_rates_from_pos("GBPJPY", mt5.TIMEFRAME_D1, 0, 2000)
    mt5.shutdown()
    return [(datetime.fromtimestamp(int(x['time']), tz=timezone.utc),
             float(x['open']), float(x['high']), float(x['low']), float(x['close']))
            for x in r]

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
        print(f"{'ALL':>6} {tn:>6} {100*th/tn:>6.1f}% {tm/tn/0.01:>9.1f}   neg_years={neg}")
    print()

def main():
    b = load_d1()
    print(f"D1: {len(b)} bars {b[0][0].date()} -> {b[-1][0].date()}\n")
    swp, fallback = [], []
    for i in range(2, len(b)):
        t2, o2, h2, l2, c2 = b[i-2]   # prior day
        t1, o1, h1, l1, c1 = b[i-1]   # signal day
        t0, o0, hh, ll, c0 = b[i]     # trade day
        inside = l2 < c1 < h2
        sw_hi = h1 > h2 and inside
        sw_lo = l1 < l2 and inside
        today = c0 - o0
        if sw_hi and sw_lo:
            continue                   # ambiguous outside bar: skipped
        if sw_hi or sw_lo:
            bias = -1 if sw_hi else 1
            swp.append((t0.year, 1 if bias * today > 0 else 0, bias * today))
        else:
            body = c1 - o1
            if body == 0: continue
            bias = 1 if body > 0 else -1
            fallback.append((t0.year, 1 if bias * today > 0 else 0, bias * today))
    show("H3a: sweep-reversal days only", swp)
    show("H3b fallback part: continuation on non-sweep days", fallback)
    show("H3b combined: sweep-reversal + continuation fallback", swp + fallback)

if __name__ == "__main__":
    main()
