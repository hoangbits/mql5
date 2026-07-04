"""Core-hypothesis autopsy: does GBPJPY daily-bias continuation exist?

CatBa's premise: yesterday's D1 direction (open vs close) predicts today's
direction. Test it directly on D1 bars, per year, with and without the
body-size filter, WITHOUT any EA mechanics (EMA, pivots, BE, sizing).

Reads D1 via the MetaTrader5 API from the running/auto-launched terminal.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
import sys
from collections import defaultdict

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"
SYM = "GBPJPY"

def main():
    if not mt5.initialize(path=PATH):
        print("INIT FAIL", mt5.last_error()); sys.exit(1)
    mt5.symbol_select(SYM, True)
    # terminal caps position-based requests at ~2000 bars -> 2018-10 onward.
    # (2016-2018 can be aggregated from the M1 cache once the grind completes.)
    rates = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_D1, 0, 2000)
    mt5.shutdown()
    if rates is None or len(rates) == 0:
        print("NO D1 DATA"); sys.exit(1)

    bars = [(datetime.fromtimestamp(int(r['time']), tz=timezone.utc), float(r['open']), float(r['close']))
            for r in rates]
    bars = [b for b in bars if b[0].year >= 2015]
    print(f"D1 bars: {len(bars)}  {bars[0][0].date()} -> {bars[-1][0].date()}\n")

    # per-year continuation stats, for several body filters (pips of 0.01)
    filters = [0.0, 0.28, 0.50, 1.00]   # 0 = no filter; 0.28 = EA default
    stats = {f: defaultdict(lambda: [0, 0, 0.0]) for f in filters}  # yr -> [n, hits, sum_move_in_bias]

    for i in range(1, len(bars)):
        (t0, o0, c0), (t1, o1, c1) = bars[i-1], bars[i]
        if t1.year < 2016: continue
        body = c0 - o0
        if body == 0: continue
        bias = 1 if body > 0 else -1
        today = c1 - o1
        hit = 1 if (today > 0) == (body > 0) else 0
        move = bias * today          # signed move in bias direction (JPY price units)
        for f in filters:
            if abs(body) >= f:
                s = stats[f][t1.year]
                s[0] += 1; s[1] += hit; s[2] += move

    for f in filters:
        label = "no filter" if f == 0 else f"|body| >= {f:.2f}"
        print(f"=== bias continuation, {label} ===")
        print(f"{'Year':>6} {'Days':>6} {'Win%':>7} {'AvgMove(pips)':>14}")
        tot_n = tot_h = 0; tot_m = 0.0
        for yr in sorted(stats[f]):
            n, h, m = stats[f][yr]
            if n == 0: continue
            tot_n += n; tot_h += h; tot_m += m
            print(f"{yr:>6} {n:>6} {100.0*h/n:>6.1f}% {m/n/0.01:>13.1f}")
        if tot_n:
            print(f"{'ALL':>6} {tot_n:>6} {100.0*tot_h/tot_n:>6.1f}% {tot_m/tot_n/0.01:>13.1f}")
        print()

if __name__ == "__main__":
    main()
