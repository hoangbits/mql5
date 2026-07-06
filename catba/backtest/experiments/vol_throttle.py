"""Volatility THROTTLE for CatBa: cut position size when realized vol hits an
extreme tail. Targets 2020-style blowups (COVID V-reversals) which live in the
high-efficiency 'trend' regime — the losses a range filter can't touch.

Hypothesis: 2020's pain is in the EXTREME vol tail (vol explosion), while
2024's GAINS are in merely-high vol. If so, throttling only the tail cuts 2020
without gutting 2024. If 2024 is also in the tail, the throttle fails (same
trap as the consolidation filter).

Method: daily ATR(14) percentile vs trailing 252d (prior day, no look-ahead).
Two schemes:
  A) STEP throttle: scale=k when ATR-pct > THR, else 1.0.
  B) VOL-TARGET: scale=min(1, target/ATR) — classic vol targeting, cap at 1
     (never lever up, only cut). target = IS median ATR.
P&L scales linearly with lots (profit/commission/swap all ∝ size), so scaling
net profit by the size factor is valid. Pre-commit IS 2016-21 / OOS 2022-26.
"""
import csv, math, datetime as dt
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"
NOM = 1_600_000

def daily():
    d=defaultdict(list)
    for r in csv.reader(open(fr"{CF}\smt_GBPJPY_H1.csv")):
        if not r or r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        d[t.date()].append((float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    return [(dd,b[0][0],max(x[1] for x in b),min(x[2] for x in b),b[-1][3])
            for dd in sorted(d) for b in [d[dd]]]

def wilder(v,p):
    out=[None]*len(v); s=None; acc=0.0; cnt=0
    for i in range(len(v)):
        if v[i] is None: continue
        if s is None:
            acc+=v[i]; cnt+=1
            if cnt==p: s=acc/p; out[i]=s
        else: s=(s*(p-1)+v[i])/p; out[i]=s
    return out

def atr_features():
    """date -> (atr_prevday, pct_vs_trailing252_prevday). No look-ahead: both
    from bars that closed strictly before this date."""
    D=daily(); n=len(D); tr=[None]*n
    for i in range(1,n):
        h,l,pc=D[i][2],D[i][3],D[i-1][4]; tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    atr=wilder(tr,14)
    feat={}
    for i in range(1,n):
        a=atr[i-1]
        if not a: continue
        hist=[atr[j] for j in range(max(0,i-1-252),i-1) if atr[j]]
        pct=100*sum(1 for x in hist if x<a)/len(hist) if hist else 50
        feat[D[i][0]]=(a,pct)
    return feat

def load_trades():
    rows=[]
    for r in csv.DictReader(open(TR)):
        try:
            t=dt.datetime.strptime(r["entry_time"].strip(),"%Y.%m.%d %H:%M").date()
            pf=float(r["profit"])
        except: continue
        rows.append((t,pf))
    return rows

def stats(pairs):
    """monthly Sharpe + max drawdown% on the equity curve of monthly returns."""
    m=defaultdict(float)
    for t,p,s in pairs: m[(t.year,t.month)]+=p*s
    ks=sorted(m); v=[m[k]/NOM*100 for k in ks]
    if len(v)<3: return 0.0,0.0,0.0
    mu=sum(v)/len(v); sd=math.sqrt(sum((x-mu)**2 for x in v)/(len(v)-1))
    sh=mu/sd*math.sqrt(12) if sd else 0
    eq=1.0;peak=1.0;mdd=0.0
    for x in v: eq*=(1+x/100); peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
    net=sum(p*s for _,p,s in pairs)
    return sh,mdd*100,net

def scaled(trades, feat, scheme, thr, k, target):
    out=[]
    for t,p in trades:
        f=feat.get(t)
        s=1.0
        if f:
            a,pct=f
            if scheme=="step":  s = k if pct>thr else 1.0
            elif scheme=="vt":  s = min(1.0, target/a) if a>0 else 1.0
        out.append((t,p,s))
    return out

def peryear(scaled_pairs):
    y=defaultdict(float)
    for t,p,s in scaled_pairs: y[t.year]+=p*s
    return y

def main():
    trades=load_trades(); feat=atr_features()
    IS=lambda t: t.year<=2021
    base=[(t,p,1.0) for t,p in trades]
    bsh,bdd,bnet=stats(base)
    print(f"BASELINE  net {bnet:>9.0f}  Sharpe {bsh:.2f}  maxDD {bdd:.1f}%\n")

    # first: is 2020 pain in the EXTREME tail while 2024 gains are not?
    print("P&L by ATR-percentile band (the make-or-break question):")
    bands=[(0,50),(50,80),(80,90),(90,100)]
    for yr in (2020,2024,2022,2026):
        line=f"  {yr}: "
        for lo,hi in bands:
            s=sum(p for t,p in trades if t.year==yr and t in feat and lo<feat[t][1]<=hi)
            line+=f"[{lo}-{hi}pct {s:>+8.0f}] "
        print(line)
    print()

    # target for vol-targeting = IS median ATR
    is_atr=sorted(feat[t][0] for t,_ in trades if IS(t) and t in feat)
    target=is_atr[len(is_atr)//2]

    print(f"{'scheme':<26}{'net':>10}{'dNet':>9}{'Sharpe':>8}{'maxDD':>7}"
          f"{'IS Sh':>7}{'OOS Sh':>7}{'2020':>9}{'2024':>9}")
    def row(tag, sc):
        sh,dd,net=stats(sc)
        iss=stats([x for x in sc if IS(x[0])])[0]
        oos=stats([x for x in sc if not IS(x[0])])[0]
        y=peryear(sc)
        print(f"{tag:<26}{net:>10.0f}{net-bnet:>+9.0f}{sh:>8.2f}{dd:>6.1f}%"
              f"{iss:>7.2f}{oos:>7.2f}{y[2020]:>+9.0f}{y[2024]:>+9.0f}")
    row("baseline", base)
    for thr in (80,90,95):
        for k in (0.5,0.33,0.0):
            row(f"step pct>{thr} x{k}", scaled(trades,feat,"step",thr,k,target))
    row("vol-target (IS median)", scaled(trades,feat,"vt",0,0,target))
    print("\nGOOD = 2020 loss shrinks materially while 2024 gain and total"
          " Sharpe hold; watch IS vs OOS for overfit.")

if __name__=="__main__":
    main()
