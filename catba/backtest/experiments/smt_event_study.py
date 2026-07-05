"""SMT event study — does inter-market divergence predict GBPJPY daily bias,
on which timeframe, and for how many days (signal decay half-life)?

Data: Common\Files\smt_{GBPJPY,GBPUSD,USDJPY}_{M15,H1}.csv (2016-2026, from
the tester exporter). London-open window = server hours [9,12) (server=NY+7).

Three divergence definitions at the window (all minimal-parameter):
  A) vs GBPUSD  — GBPJPY makes window extreme the partner fails to confirm.
  B) vs USDJPY  — same, positive-corr leg.
  C) residual   — GBPJPY window return minus its OLS fit on GBPUSD+USDJPY
                  window returns (>0 = overextended up -> fade/sell).
Event study: from the window-end GBPJPY price, forward cumulative return
(pips) in the BIAS direction over horizons h = 0..10 trading days.
Read off: best TF/method (smooth positive drift) + horizon where it peaks
(= holding half-life). Also per-year at the peak horizon (consistency).
"""
import csv, datetime as dt, numpy as np
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
WIN = range(9, 12)   # London-open server hours
PIP = 0.01
HMAX = 10

def load(sym, tf):
    out = []
    with open(f"{CF}\\smt_{sym}_{tf}.csv") as f:
        r = csv.reader(f); next(r)
        for row in r:
            if len(row) < 5: continue
            t, o, h, l, c = row[0], row[1], row[2], row[3], row[4]
            out.append((int(t), float(o), float(h), float(l), float(c)))
    out.sort()
    return out

def by_day(bars):
    d = defaultdict(list)
    for b in bars:
        d[dt.datetime.utcfromtimestamp(b[0]).date()].append(b)
    return d

def window_stats(bars_day):
    w = [b for b in bars_day if dt.datetime.utcfromtimestamp(b[0]).hour in WIN]
    if len(w) < 3: return None
    o = w[0][1]; c = w[-1][4]
    hi = max(b[2] for b in w); lo = min(b[3] for b in w)
    # is the extreme "held" to the last bar (still making it)?
    last_h = w[-1][2]; last_l = w[-1][3]
    return dict(o=o, c=c, hi=hi, lo=lo, ret=c-o,
                mk_high=last_h >= hi - 1e-12, mk_low=last_l <= lo + 1e-12)

def signals(tf):
    gj = by_day(load("GBPJPY", tf)); gu = by_day(load("GBPUSD", tf)); uj = by_day(load("USDJPY", tf))
    days = sorted(set(gj) & set(gu) & set(uj))
    # GBPJPY daily closes for forward returns
    gj_close = {d: gj[d][-1][4] for d in gj}
    ordered = sorted(gj_close)
    idx = {d: i for i, d in enumerate(ordered)}
    sig = {}  # method -> list of (day, bias, window_end_price)
    for m in ("A_gbpusd", "B_usdjpy", "C_resid"):
        sig[m] = []
    # collect window returns for residual OLS
    recs = []
    for d in days:
        gjw = window_stats(gj[d]); guw = window_stats(gu[d]); ujw = window_stats(uj[d])
        if not gjw or not guw or not ujw: continue
        recs.append((d, gjw, guw, ujw))
    if not recs: return sig, gj_close, ordered, idx
    # OLS: gj_ret ~ gu_ret + uj_ret  (in pips)
    X = np.array([[r[2]['ret'], r[3]['ret']] for r in recs])
    y = np.array([r[1]['ret'] for r in recs])
    Xc = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    for d, gjw, guw, ujw in recs:
        # A vs GBPUSD: GJ makes new high, GU does not (bearish->sell); mirror
        if gjw['mk_high'] and not guw['mk_high']: sig['A_gbpusd'].append((d, -1, gjw['c']))
        elif gjw['mk_low'] and not guw['mk_low']:  sig['A_gbpusd'].append((d, +1, gjw['c']))
        # B vs USDJPY
        if gjw['mk_high'] and not ujw['mk_high']: sig['B_usdjpy'].append((d, -1, gjw['c']))
        elif gjw['mk_low'] and not ujw['mk_low']:  sig['B_usdjpy'].append((d, +1, gjw['c']))
        # C residual: gj_ret - fit ; >0 overextended up -> sell
        fit = beta[0] + beta[1]*guw['ret'] + beta[2]*ujw['ret']
        resid = gjw['ret'] - fit
        thr = 0.15  # ~15 pip residual threshold (minimal param)
        if resid > thr:  sig['C_resid'].append((d, -1, gjw['c']))
        elif resid < -thr: sig['C_resid'].append((d, +1, gjw['c']))
    return sig, gj_close, ordered, idx

def event_curve(sig_list, gj_close, ordered, idx):
    # returns array [HMAX+1] of mean pips in bias dir, and win% at each horizon
    means = []; wins = []; ns = []
    peryear_peak = defaultdict(list)
    for h in range(HMAX+1):
        vals = []
        for d, bias, px in sig_list:
            i = idx[d]
            if i + h >= len(ordered): continue
            fwd = gj_close[ordered[i+h]] - px
            vals.append(bias * fwd / PIP)
        vals = np.array(vals)
        means.append(vals.mean() if len(vals) else 0.0)
        wins.append(100*np.mean(vals > 0) if len(vals) else 0.0)
        ns.append(len(vals))
    return np.array(means), np.array(wins), ns

def main():
    print("SMT EVENT STUDY — forward cum return (pips) in bias direction\n")
    for tf in ("M5", "M15", "M30", "H1"):
        sig, gj_close, ordered, idx = signals(tf)
        print(f"================= TF = {tf} =================")
        for m, lst in sig.items():
            if len(lst) < 50:
                print(f"  {m}: only {len(lst)} signals, skip"); continue
            means, wins, ns = event_curve(lst, gj_close, ordered, idx)
            peak_h = int(np.argmax(means))
            print(f"  {m}: {len(lst)} signals")
            print(f"    h:    " + " ".join(f"{h:>6}" for h in range(HMAX+1)))
            print(f"    pips: " + " ".join(f"{means[h]:>6.1f}" for h in range(HMAX+1)))
            print(f"    win%: " + " ".join(f"{wins[h]:>6.1f}" for h in range(HMAX+1)))
            print(f"    -> peak drift at h={peak_h} ({means[peak_h]:+.1f} pips, "
                  f"win {wins[peak_h]:.1f}%, n={ns[peak_h]})")
        print()

if __name__ == "__main__":
    main()
