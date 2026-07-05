"""2-instrument portfolio: does GBPJPY + AUDJPY (ema13+minStop30) beat GBPJPY
alone on Sharpe / drawdown / durability (Darwinex's weak spots)?

Both fixed 0.10 lot (comparable JPY). Combine monthly returns at several
capital weightings. If NO weighting improves Sharpe or spreads returns,
AUDJPY's near-breakeven edge just dilutes and diversification doesn't help.
"""
import csv, math, datetime as dt
from collections import defaultdict

GBP = r"C:\Users\giaho\repos\mql5\catba\backtest\results\ref13ms_trades.csv"
AUD = r"C:\Users\giaho\repos\mql5\catba\backtest\results\audjpy_trades.csv"
NOM = 1_600_000

def monthly(path):
    m = defaultdict(float)
    for r in csv.DictReader(open(path)):
        try:
            t = dt.datetime.strptime(r["close_time"].strip(), "%Y.%m.%d %H:%M")
            m[(t.year,t.month)] += float(r["profit"])+float(r["swap"])+float(r["commission"])
        except Exception: continue
    return m

def grid(*ms):
    keys=set()
    for m in ms: keys|=set(m)
    y0,mo0=min(keys); y1,mo1=max(keys)
    out=[]; y,mo=y0,mo0
    while (y,mo)<=(y1,mo1):
        out.append((y,mo)); mo+=1
        if mo==13: mo=1; y+=1
    return out

def stats(rets):
    n=len(rets); mean=sum(rets)/n
    sd=math.sqrt(sum((x-mean)**2 for x in rets)/(n-1)) if n>1 else 0
    sharpe=mean/sd*math.sqrt(12) if sd else 0
    # max drawdown of cumulative
    eq=1.0; peak=1.0; mdd=0
    for r in rets:
        eq*= (1+r); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
    return sharpe, mdd*100, 100*sum(1 for x in rets if x>0)/n

def yearly(gkeys, series):
    y=defaultdict(float)
    for (yr,mo),v in zip(gkeys,series): y[yr]+=v
    return y

def main():
    g=monthly(GBP); a=monthly(AUD)
    keys=grid(g,a)
    gr=[g.get(k,0)/NOM for k in keys]   # GBPJPY monthly return
    ar=[a.get(k,0)/NOM for k in keys]   # AUDJPY monthly return
    # correlation
    n=len(keys); mg=sum(gr)/n; ma=sum(ar)/n
    cov=sum((gr[i]-mg)*(ar[i]-ma) for i in range(n))/n
    sg=math.sqrt(sum((x-mg)**2 for x in gr)/n); sa=math.sqrt(sum((x-ma)**2 for x in ar)/n)
    corr=cov/(sg*sa) if sg and sa else 0
    print(f"GBPJPY vs AUDJPY monthly-return correlation: {corr:+.2f}\n")
    print(f"{'weight (G/A)':>14}{'Sharpe':>8}{'maxDD%':>8}{'pos-mo%':>9}{'net%':>8}{'greenYr':>9}")
    for w in (1.0, 0.8, 0.7, 0.6, 0.5):
        port=[w*gr[i]+(1-w)*ar[i] for i in range(n)]
        sh,mdd,pm=stats(port)
        yr=yearly(keys,port); gy=sum(1 for v in yr.values() if v>0)
        print(f"{int(w*100):>6}/{int((1-w)*100):<7}{sh:>8.2f}{mdd:>8.1f}{pm:>8.1f}%{sum(port)*100:>7.1f}{gy:>6}/{len(yr)}")
    print("\n(w=100/0 = GBPJPY alone, the benchmark)")

if __name__=="__main__":
    main()
