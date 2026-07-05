"""Phase 3.3 — honest statistics for the CatBa reference config.

From ref_trades.csv (1704 closing deals, fixed 0.10 lot, BE 0.3xATR):
 - monthly P&L series -> annualized Sharpe/Sortino (full, IS 2016-22, OOS 2023-26)
 - skew/kurtosis, % positive months
 - PSR(0): probability true Sharpe > 0 (Bailey & Lopez de Prado)
 - DSR: Sharpe deflated for N~78 trials + non-normality (the overfitting haircut)

Sharpe of a fixed-lot P&L series is scale-invariant to lot size, so these
numbers describe the edge itself, independent of the 0.5%/1%/2% risk dial.
"""
import csv, math, datetime as dt
from collections import defaultdict
from statistics import NormalDist

TRADES = r"C:\Users\giaho\repos\mql5\catba\backtest\results\ref_trades.csv"
N_TRIALS = 78          # running trial count from JOURNAL
NOMINAL = 1_600_000    # JPY nominal (for % framing)
GAMMA = 0.5772156649   # Euler-Mascheroni
Z = NormalDist().inv_cdf
PHI = NormalDist().cdf

def load_monthly():
    m = defaultdict(float)
    with open(TRADES) as f:
        for r in csv.DictReader(f):
            try:
                t = dt.datetime.strptime(r["close_time"].strip(), "%Y.%m.%d %H:%M")
                net = float(r["profit"]) + float(r["swap"]) + float(r["commission"])
            except Exception:
                continue
            m[(t.year, t.month)] += net
    # fill the full month grid (zeros where no trades) for a correct Sharpe
    if not m: return [], []
    keys = sorted(m)
    y0, mo0 = keys[0]; y1, mo1 = keys[-1]
    months = []
    y, mo = y0, mo0
    while (y, mo) <= (y1, mo1):
        months.append((y, mo, m.get((y, mo), 0.0)))
        mo += 1
        if mo == 13: mo = 1; y += 1
    return months

def stats(rets):
    n = len(rets)
    mean = sum(rets)/n
    var = sum((x-mean)**2 for x in rets)/(n-1)
    sd = math.sqrt(var) if var > 0 else 0
    sr_m = mean/sd if sd else 0                      # per-month Sharpe
    sr_ann = sr_m*math.sqrt(12)
    # downside dev (Sortino)
    dn = [min(0, x-0)**2 for x in rets]
    dd = math.sqrt(sum(dn)/n)
    sortino = (mean/dd)*math.sqrt(12) if dd else float('nan')
    # skew / excess kurtosis
    if sd:
        sk = sum((x-mean)**3 for x in rets)/n/sd**3
        ku = sum((x-mean)**4 for x in rets)/n/sd**4   # raw kurtosis
    else:
        sk = ku = 0
    return dict(n=n, mean=mean, sd=sd, sr_m=sr_m, sr_ann=sr_ann, sortino=sortino,
                skew=sk, kurt=ku, pos=100*sum(1 for x in rets if x>0)/n, total=sum(rets))

def psr(sr_m, sr_bench, T, skew, kurt):
    denom = math.sqrt(max(1e-9, 1 - skew*sr_m + (kurt-1)/4*sr_m**2))
    return PHI((sr_m - sr_bench)*math.sqrt(T-1)/denom)

def main():
    months = load_monthly()
    rets = [pnl for _,_,pnl in months]
    full = stats(rets)
    IS  = stats([p for y,_,p in months if y <= 2022])
    OOS = stats([p for y,_,p in months if y >= 2023])

    def line(tag, s):
        print(f"  {tag:<14} n={s['n']:>3}mo  Sharpe(ann)={s['sr_ann']:>5.2f}  "
              f"Sortino={s['sortino']:>5.2f}  pos={s['pos']:>4.1f}%  "
              f"net={s['total']/NOMINAL*100:>+6.1f}%")
    print("=== CatBa reference config — risk-adjusted stats (fixed 0.10 lot) ===")
    line("FULL 2016-26", full); line("IS 2016-22", IS); line("OOS 2023-26", OOS)

    # PSR (prob true Sharpe>0) on full sample
    p0 = psr(full['sr_m'], 0.0, full['n'], full['skew'], full['kurt'])
    # DSR: benchmark = expected max Sharpe under null across N trials
    # estimate trial-Sharpe variance from the dispersion of yearly Sharpes
    yr = defaultdict(list)
    for y,_,p in months: yr[y].append(p)
    yr_sr = [stats(v)['sr_m'] for v in yr.values() if len(v) > 1]
    v_sr = (sum((x-sum(yr_sr)/len(yr_sr))**2 for x in yr_sr)/(len(yr_sr)-1)) if len(yr_sr) > 1 else 1.0/full['n']
    sr_star = math.sqrt(v_sr)*((1-GAMMA)*Z(1-1.0/N_TRIALS) + GAMMA*Z(1-1.0/(N_TRIALS*math.e)))
    dsr = psr(full['sr_m'], sr_star, full['n'], full['skew'], full['kurt'])
    print(f"\n  PSR(true SR>0)         = {p0*100:>5.1f}%   (skew={full['skew']:+.2f}, kurt={full['kurt']:.1f})")
    print(f"  N trials               = {N_TRIALS}")
    print(f"  SR* (null max, monthly)= {sr_star:.3f}   (trial-SR var est {v_sr:.4f})")
    print(f"  DSR (haircut vs SR*)   = {dsr*100:>5.1f}%   <- prob edge is real after {N_TRIALS}-trial haircut")
    print(f"\n  KEY: OOS 2023-26 Sharpe = {OOS['sr_ann']:.2f} (untouched holdout — the honest number)")

if __name__ == "__main__":
    main()
