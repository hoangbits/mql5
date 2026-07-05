"""S1 screen for H14: structural regime gate (ADX / ATR-slope) on D1.

Pre-registered (QUEUE.md):
  Continuation bias (yesterday's D1 direction) traded ONLY when the
  market STATE qualifies:
    - ADX(14,D1) > thr, thr in {20, 25}
    - ATR(14,D1) today > ATR(14,D1) 20 days ago (rising-vol regime)
  Baseline for comparison: unconditional continuation (52.2% / +4.9).
  Metric: today open->close in bias direction (pips of 0.01), per year.
  No other variants; ADX/ATR computed here (not via MT5) for transparency.
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

def wilder(vals, period, seed_len):
    """Wilder smoothing; vals indexed same as bars, first seed_len are None-ish."""
    out = [None]*len(vals)
    # simple average seed
    s = None
    for i in range(len(vals)):
        if vals[i] is None:
            continue
        if s is None:
            # collect seed
            window = [v for v in vals[max(0,i-period+1):i+1] if v is not None]
            if len([v for v in vals[:i+1] if v is not None]) >= period:
                s = sum(vals[i-period+1:i+1]) / period
                out[i] = s
        else:
            s = (s*(period-1) + vals[i]) / period
            out[i] = s
    return out

def compute_atr_adx(b, period=14):
    n = len(b)
    tr = [None]*n; pdm = [None]*n; ndm = [None]*n
    for i in range(1, n):
        h, l, pc = b[i][2], b[i][3], b[i-1][4]
        tr[i] = max(h-l, abs(h-pc), abs(l-pc))
        up = b[i][2]-b[i-1][2]; dn = b[i-1][3]-b[i][3]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        ndm[i] = dn if (dn > up and dn > 0) else 0.0
    atr = wilder(tr, period, period)
    spdm = wilder(pdm, period, period)
    sndm = wilder(ndm, period, period)
    pdi = [None]*n; ndi = [None]*n; dx = [None]*n
    for i in range(n):
        if atr[i] and atr[i] > 0 and spdm[i] is not None:
            pdi[i] = 100*spdm[i]/atr[i]; ndi[i] = 100*sndm[i]/atr[i]
            s = pdi[i]+ndi[i]
            dx[i] = 100*abs(pdi[i]-ndi[i])/s if s > 0 else 0.0
    adx = wilder(dx, period, period)
    return atr, adx

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
    atr, adx = compute_atr_adx(b, 14)
    print(f"D1: {len(b)} bars {b[0][0].date()} -> {b[-1][0].date()}\n")

    def cont_rows(gate):
        rows = []
        for i in range(1, len(b)):
            body = b[i-1][4] - b[i-1][1]
            if body == 0: continue
            if not gate(i): continue
            bias = 1 if body > 0 else -1
            today = b[i][4] - b[i][1]
            rows.append((b[i][0].year, 1 if bias*today > 0 else 0, bias*today))
        return rows

    show("baseline: unconditional continuation", cont_rows(lambda i: True))
    for thr in (20, 25):
        show(f"H14 ADX(14) > {thr} at signal day i-1",
             cont_rows(lambda i, t=thr: adx[i-1] is not None and adx[i-1] > t))
    show("H14 ATR rising: ATR[i-1] > ATR[i-21]",
         cont_rows(lambda i: i-21 >= 0 and atr[i-1] and atr[i-21] and atr[i-1] > atr[i-21]))

if __name__ == "__main__":
    main()
