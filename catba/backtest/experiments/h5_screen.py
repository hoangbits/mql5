"""S1 screen for H5: D1 Fair Value Gap displacement bias.

Pre-registered (QUEUE.md):
  Bullish FVG on days (i-2,i-1,i): high[i-2] < low[i]  (gap spans bar i-1's
  displacement). Bearish mirror: low[i-2] > high[i].
  Signal for day i+1: displacement direction, valid only if close[i] has
  not encroached past the gap's 50% (consequent encroachment).
  Min gap size variants: {0.00, 0.10, 0.20} JPY. No other variants.
Metric: day i+1 open->close in bias direction (pips of 0.01), per year.
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
    for min_gap in (0.00, 0.10, 0.20):
        rows = []
        for i in range(2, len(b) - 1):
            h2, l2 = b[i-2][2], b[i-2][3]
            hi, li, ci = b[i][2], b[i][3], b[i][4]
            t1, o1, c1 = b[i+1][0], b[i+1][1], b[i+1][4]
            bias = 0
            if h2 < li and (li - h2) >= min_gap:          # bullish FVG
                ce = (h2 + li) / 2.0
                if ci > ce:                                # not encroached past 50%
                    bias = 1
            elif l2 > hi and (l2 - hi) >= min_gap:        # bearish FVG
                ce = (l2 + hi) / 2.0
                if ci < ce:
                    bias = -1
            if bias:
                mv = bias * (c1 - o1)
                rows.append((t1.year, 1 if mv > 0 else 0, mv))
        show(f"H5 FVG bias, min gap {min_gap:.2f}", rows)

if __name__ == "__main__":
    main()
