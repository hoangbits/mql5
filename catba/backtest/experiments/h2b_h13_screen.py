"""S1 screens for H2b (regime fade-switch) and H13 (day-type router).

Pre-registered (QUEUE.md):
  H2b: trailing 40d continuation win-rate: <0.45 -> FADE bias;
       0.45..0.50 -> flat; >0.50 -> continuation. Robustness peek: W=60.
  H13: signal day swept PDH/PDL & closed inside prior range -> FADE;
       non-sweep day and 0.10<=|body(signal day)|<=0.60 -> continuation;
       else flat. Parameters inherited from H1/H3; no new tuning.
Metric: open->close move in traded direction (pips of 0.01), per year.
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

    # per-day continuation info
    cont = {}   # i -> (bias, hit, today_move_signed_by_bias)
    for i in range(1, len(b)):
        body = b[i-1][4] - b[i-1][1]
        if body == 0: continue
        bias = 1 if body > 0 else -1
        today = b[i][4] - b[i][1]
        cont[i] = (bias, 1 if bias * today > 0 else 0, bias * today)

    print("================ H2b: regime fade-switch ================")
    for W in (40, 60):
        rows = []
        for i in sorted(cont):
            w = [cont[j][1] for j in range(i - W, i) if j in cont]
            if len(w) < int(W * 0.8): continue
            wr = sum(w) / len(w)
            bias, hit, mv = cont[i]
            if wr > 0.50:
                rows.append((b[i][0].year, hit, mv))            # continuation
            elif wr < 0.45:
                rows.append((b[i][0].year, 1 - hit, -mv))       # fade
            # 0.45..0.50 -> flat
        show(f"H2b switch W={W} (<0.45 fade, >0.50 cont)", rows)

    print("================ H13: day-type router ================")
    rows = []; n_sweep = n_cont = 0
    for i in range(2, len(b)):
        t2, o2, h2, l2, c2 = b[i-2]
        t1, o1, h1, l1, c1 = b[i-1]
        t0, o0, hh, ll, c0 = b[i]
        today = c0 - o0
        inside = l2 < c1 < h2
        sw_hi = h1 > h2 and inside
        sw_lo = l1 < l2 and inside
        body = c1 - o1
        if sw_hi and sw_lo:
            continue
        if sw_hi or sw_lo:
            bias = -1 if sw_hi else 1                            # fade the sweep
            rows.append((t0.year, 1 if bias * today > 0 else 0, bias * today))
            n_sweep += 1
        elif body != 0 and 0.10 <= abs(body) <= 0.60:
            bias = 1 if body > 0 else -1                         # continuation
            rows.append((t0.year, 1 if bias * today > 0 else 0, bias * today))
            n_cont += 1
    print(f"(router mix: {n_sweep} sweep-fade days, {n_cont} continuation days)")
    show("H13 router: sweep->fade | moderate-body->continuation | else flat", rows)

if __name__ == "__main__":
    main()
