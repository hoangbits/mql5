"""S1 screens for H1 (body-size cap/inversion) and H2 (rolling regime gate).

Pre-registered variants ONLY (QUEUE.md):
  H1: minCap in {0.00, 0.10} x maxCap in {0.60, 1.00, 1.50}
  H2: window in {40, 60, 90} x threshold in {0.50, 0.55}
Baselines: no filter (52.2% / +4.9), current floor >=0.28.
Metric: close-to-close continuation win% and avg signed move (pips of 0.01),
per year. Keep criteria (S1): beat baseline overall AND >=7/9 years
non-negative AND helps/neutral in 2019 & 2025.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone
from collections import defaultdict
import sys

PATH = r"C:\Program Files\Darwinex MetaTrader 5\terminal64.exe"

def load_d1():
    assert mt5.initialize(path=PATH), mt5.last_error()
    mt5.symbol_select("GBPJPY", True)
    r = mt5.copy_rates_from_pos("GBPJPY", mt5.TIMEFRAME_D1, 0, 2000)
    mt5.shutdown()
    assert r is not None and len(r), "no D1"
    return [(datetime.fromtimestamp(int(x['time']), tz=timezone.utc),
             float(x['open']), float(x['close'])) for x in r]

def yearly(rows):  # rows: list of (year, hit, move)
    by = defaultdict(lambda: [0, 0, 0.0])
    for y, h, m in rows:
        s = by[y]; s[0] += 1; s[1] += h; s[2] += m
    return by

def show(name, rows):
    by = yearly(rows)
    print(f"--- {name} ---")
    print(f"{'Year':>6} {'Days':>6} {'Win%':>7} {'Avg(pips)':>10}")
    tn = th = 0; tm = 0.0
    neg_years = []
    for y in sorted(by):
        n, h, m = by[y]
        avg = m / n / 0.01
        if avg < 0: neg_years.append(y)
        tn += n; th += h; tm += m
        print(f"{y:>6} {n:>6} {100*h/n:>6.1f}% {avg:>9.1f}")
    if tn:
        print(f"{'ALL':>6} {tn:>6} {100*th/tn:>6.1f}% {tm/tn/0.01:>9.1f}   neg_years={neg_years}")
    print()

def main():
    bars = load_d1()
    print(f"D1: {len(bars)} bars {bars[0][0].date()} -> {bars[-1][0].date()}\n")

    # daily continuation outcomes
    days = []  # (year, bias(+1/-1), hit, signed_move, |body_yesterday|)
    for i in range(1, len(bars)):
        (t0, o0, c0), (t1, o1, c1) = bars[i-1], bars[i]
        body = c0 - o0
        if body == 0: continue
        bias = 1 if body > 0 else -1
        today = c1 - o1
        days.append((t1.year, bias, 1 if (today > 0) == (body > 0) else 0,
                     bias * today, abs(body), i))

    print("================ H1: body cap/inversion ================")
    show("baseline: no filter", [(y, h, m) for y, b, h, m, ab, i in days])
    show("current: floor >=0.28", [(y, h, m) for y, b, h, m, ab, i in days if ab >= 0.28])
    for mn in (0.00, 0.10):
        for mx in (0.60, 1.00, 1.50):
            rows = [(y, h, m) for y, b, h, m, ab, i in days if mn <= ab <= mx]
            show(f"H1 cap: {mn:.2f} <= |body| <= {mx:.2f}", rows)

    print("================ H2: rolling regime gate ================")
    # continuation outcome list indexed by bar i (known after day i closes)
    out_by_i = {i: h for y, b, h, m, ab, i in days}
    for W in (40, 60, 90):
        for thr in (0.50, 0.55):
            rows = []
            for y, b, h, m, ab, i in days:
                # trailing window strictly before day i
                w = [out_by_i[j] for j in range(i - W, i) if j in out_by_i]
                if len(w) < int(W * 0.8): continue
                if sum(w) / len(w) > thr:
                    rows.append((y, h, m))
            show(f"H2 gate: win-rate({W}d) > {thr:.2f}", rows)

if __name__ == "__main__":
    main()
