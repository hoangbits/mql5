"""Monte-Carlo drawdown / risk-of-ruin for the CatBa reference config.

Input: ref_trades.csv (fixed 0.10 lot, BE 0.3xATR). 1 pip = 100 JPY.
Each trade -> net pips. At risk r%, per-trade equity return (fixed-ref-stop
sizing, refStopPips=70) = (r/100) * (pips/70).

Two resamplers:
  - RESHUFFLE  (i.i.d. assumption; OPTIMISTIC — breaks regime clustering)
  - BLOCK BOOTSTRAP (block=30 trades ~ preserves losing-streak clustering)
Reports max-drawdown distribution and P(ruin) at each risk level, plus
Kelly-optimal sizing. Deterministic (fixed seed).
"""
import csv, numpy as np

REF_STOP = 70.0
SEED = 12345
N_SIM = 20000
BLOCK = 30
RISKS = [0.5, 1.0, 2.0]

def load_pips(path):
    pips = []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                net = float(row["profit"]) + float(row["swap"]) + float(row["commission"])
            except (ValueError, KeyError):
                continue
            pips.append(net / 100.0)   # 0.10 lot: 1 pip = 100 JPY
    return np.array(pips)

def max_dd(path_equity):
    peak = np.maximum.accumulate(path_equity)
    return np.max((peak - path_equity) / peak)

def simulate(pips, r, resampler, rng):
    ret_unit = pips / REF_STOP * (r / 100.0)   # per-trade equity return at risk r
    n = len(ret_unit)
    dds = np.empty(N_SIM); finals = np.empty(N_SIM)
    for s in range(N_SIM):
        seq = resampler(ret_unit, n, rng)
        eq = np.cumprod(1.0 + seq)
        dds[s] = max_dd(np.concatenate([[1.0], eq]))
        finals[s] = eq[-1] - 1.0
    return dds, finals

def reshuffle(ret, n, rng):
    return rng.permutation(ret)

def block_boot(ret, n, rng):
    nb = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, len(ret) - BLOCK + 1, size=nb)
    return np.concatenate([ret[s:s+BLOCK] for s in starts])[:n]

def kelly(pips):
    # maximize E[log(1 + f * x)] where x = pips/REF_STOP (per-trade return at 1x ref risk)
    x = pips / REF_STOP
    fs = np.linspace(0.001, 0.30, 600)
    best_f, best_g = 0, -1e9
    for f in fs:
        v = 1.0 + f * x
        if np.any(v <= 0): continue
        g = np.mean(np.log(v))
        if g > best_g: best_g, best_f = g, f
    return best_f  # f is risk fraction per trade on the ref-stop unit == risk% /100 *? -> f*100 = risk%

def main():
    pips = load_pips(r"C:\Users\giaho\repos\mql5\catba\backtest\results\ref_trades.csv")
    print(f"trades={len(pips)}  mean={pips.mean():.2f} pips  median={np.median(pips):.2f}  "
          f"win%={100*np.mean(pips>0):.1f}  sum={pips.sum():.0f} pips\n")

    f = kelly(pips)
    print(f"KELLY-optimal risk/trade ~ {f*100:.2f}%   (half-Kelly ~ {f*50:.2f}%)")
    print(f"  -> our 0.5% default is ~{0.5/(f*100):.2f}x Kelly "
          f"({'below' if 0.5 < f*100 else 'above'} full Kelly)\n")

    rng = np.random.default_rng(SEED)
    print(f"{'risk':>5} {'method':>7} | {'medDD':>6} {'95%DD':>6} {'99%DD':>6} {'maxDD':>6} | "
          f"{'medRet':>7} {'P(end<0)':>9} {'P(DD>20%)':>10} {'P(DD>30%)':>10} {'P(DD>50%)':>10}")
    for r in RISKS:
        for name, fn in [("reshuf", reshuffle), ("block", block_boot)]:
            dds, finals = simulate(pips, r, fn, rng)
            print(f"{r:>4.1f}% {name:>7} | "
                  f"{100*np.median(dds):>5.1f}% {100*np.percentile(dds,95):>5.1f}% "
                  f"{100*np.percentile(dds,99):>5.1f}% {100*np.max(dds):>5.1f}% | "
                  f"{100*np.median(finals):>6.1f}% {100*np.mean(finals<0):>8.1f}% "
                  f"{100*np.mean(dds>0.20):>9.1f}% {100*np.mean(dds>0.30):>9.1f}% "
                  f"{100*np.mean(dds>0.50):>9.1f}%")
    print("\nNote: RESHUFFLE assumes i.i.d. trades (optimistic — breaks regime")
    print("clustering). BLOCK bootstrap preserves ~2-month streaks and is the")
    print("more honest drawdown estimate. Historical actual maxDD at 0.5% ~ 11%.")

if __name__ == "__main__":
    main()
