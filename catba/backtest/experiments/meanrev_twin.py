"""Mean-reversion 'twin' for CatBa: sweep-reversal (H3), framed as a HEDGE.
Test whether combining it with CatBa (continuation) yields a durable,
higher-Sharpe stream (the Darwinex durability fix).

MR signal (daily): if prior day raided the day-before's high/low and closed
back INSIDE that range (turtle soup), fade -> bias for today; trade day
open->close. Proxy (no stop) for a first-pass combination test.
Combine with CatBa monthly returns, equal-risk (unit-vol) weighting.
"""
import csv, math, datetime as dt
from collections import defaultdict

H1 = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files\smt_GBPJPY_H1.csv"
CATBA = r"C:\Users\giaho\repos\mql5\catba\backtest\results\ref13ms_trades.csv"
PIP=0.01; NOM=1_600_000

def daily_from_h1():
    d=defaultdict(list)
    for r in csv.reader(open(H1)):
        if r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        d[t.date()].append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    days=[]
    for dd in sorted(d):
        b=sorted(d[dd]); days.append((dd,b[0][1],max(x[2] for x in b),min(x[3] for x in b),b[-1][4]))
    return days  # date,o,h,l,c

def mr_monthly():
    D=daily_from_h1(); m=defaultdict(float)
    for i in range(2,len(D)):
        _,o2,h2,l2,c2=D[i-2]; _,o1,h1,l1,c1=D[i-1]; dt0,o0,hh,ll,c0=D[i]
        inside=l2<c1<h2
        sw_hi=h1>h2 and inside; sw_lo=l1<l2 and inside
        if sw_hi and sw_lo: continue
        bias=-1 if sw_hi else (1 if sw_lo else 0)
        if not bias: continue
        m[(dt0.year,dt0.month)] += bias*(c0-o0)/PIP   # pips
    return m

def catba_monthly():
    m=defaultdict(float)
    for r in csv.DictReader(open(CATBA)):
        try:
            t=dt.datetime.strptime(r["close_time"].strip(),"%Y.%m.%d %H:%M")
            m[(t.year,t.month)]+=float(r["profit"])+float(r["swap"])+float(r["commission"])
        except: pass
    return m

def stats(x):
    n=len(x); mu=sum(x)/n; sd=math.sqrt(sum((v-mu)**2 for v in x)/(n-1))
    sh=mu/sd*math.sqrt(12) if sd else 0
    eq=1;peak=1;mdd=0
    for v in x: eq*= (1+v/100); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
    return sh,mdd*100,100*sum(1 for v in x if v>0)/n

def main():
    cb=catba_monthly(); mr=mr_monthly()
    keys=sorted(set(cb)&set(mr))
    cbv=[cb[k]/NOM*100 for k in keys]     # CatBa monthly return %
    mrv=[mr[k] for k in keys]             # MR monthly pips
    # correlation
    n=len(keys); mc=sum(cbv)/n; mm=sum(mrv)/n
    cov=sum((cbv[i]-mc)*(mrv[i]-mm) for i in range(n))/n
    sc=math.sqrt(sum((v-mc)**2 for v in cbv)/n); sm=math.sqrt(sum((v-mm)**2 for v in mrv)/n)
    corr=cov/(sc*sm) if sc and sm else 0
    # normalize both to unit monthly vol (equal risk), then combine
    cbn=[v/sc for v in cbv]; mrn=[v/sm for v in mrv]
    print(f"months={n}  CatBa vs MeanRev monthly-return correlation = {corr:+.2f}")
    print(f"  (negative = good hedge; MR standalone Sharpe {stats(mrv)[0]:.2f})\n")
    print(f"{'weight C/M':>12}{'Sharpe':>8}{'maxDD%':>8}{'pos-mo%':>9}{'greenYr':>9}")
    for w in (1.0,0.8,0.7,0.6,0.5):
        port=[w*cbn[i]+(1-w)*mrn[i] for i in range(n)]
        sh,mdd,pm=stats(port)
        yr=defaultdict(float)
        for i,k in enumerate(keys): yr[k[0]]+=port[i]
        gy=sum(1 for v in yr.values() if v>0)
        print(f"{int(w*100):>5}/{int((1-w)*100):<6}{sh:>8.2f}{mdd:>8.1f}{pm:>8.1f}%{gy:>6}/{len(yr)}")
    print("\n(w=100/0 = CatBa alone; normalized to unit vol so Sharpe is comparable)")

if __name__=="__main__":
    main()
