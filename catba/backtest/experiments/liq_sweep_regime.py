"""Liquidity-sweep consolidation detector (ICT accumulation vs displacement),
learned over 10y GBPJPY, to filter CatBa's chop years (2018/2020/2026) without
killing the trend years (2022/2024).

CONCEPT (ICT): consolidation = price raids liquidity on BOTH sides of a range
and reverts (two-sided stop-hunts, low path efficiency). Expansion/trend =
price sweeps ONE side then DISPLACES and holds (high efficiency). CatBa is a
continuation system -> should skip consolidation, trade expansion.

Two economically-grounded, low-knob detectors, per detection timeframe:
  A) Kaufman Efficiency Ratio (ER) = |net move| / sum(|bar moves|) over W.
     Low ER = choppy/consolidation, high ER = trending. (single knob: W)
  B) Two-sided sweep count: in last W bars, count reverted raids of prior
     swing highs AND swing lows. Consolidation = both sides raided & inside
     range. (knobs: pivot k, W)

DISCIPLINE: pre-commit IS 2016-2021 / OOS 2022-2026. Choose threshold on IS
(percentile, not fit-to-PnL), lock, report OOS. Focus on losing years.
"""
import csv, math, datetime as dt
from collections import defaultdict

CF = r"C:\Users\giaho\AppData\Roaming\MetaQuotes\Terminal\Common\Files"
TR = r"C:\Users\giaho\repos\mql5\catba\backtest\results\tradesx_ema13.csv"

def load_bars(tf):
    f = fr"{CF}\smt_GBPJPY_{tf}.csv"
    out=[]
    for r in csv.reader(open(f)):
        if not r or r[0]=="time": continue
        t=dt.datetime.utcfromtimestamp(int(r[0]))
        out.append((t,float(r[1]),float(r[2]),float(r[3]),float(r[4])))
    return out  # time,o,h,l,c

def resample(bars, unit):
    """unit: 'D'=calendar day, 'H4'=4h buckets, 'H1'=pass-through(if H1)."""
    if unit=="H1": return bars
    d=defaultdict(list)
    for b in bars:
        t=b[0]
        if unit=="D": key=t.date()
        elif unit=="H4": key=(t.date(), t.hour//4)
        else: raise ValueError(unit)
        d[key].append(b)
    out=[]
    for k in sorted(d, key=lambda x: d[x][0][0]):
        g=sorted(d[k]); out.append((g[0][0], g[0][1], max(x[2] for x in g),
                                     min(x[3] for x in g), g[-1][4]))
    return out

def wilder(v,p):
    out=[None]*len(v); s=None; acc=0.0; cnt=0
    for i in range(len(v)):
        if v[i] is None: continue
        if s is None:
            acc+=v[i]; cnt+=1
            if cnt==p: s=acc/p; out[i]=s
        else:
            s=(s*(p-1)+v[i])/p; out[i]=s
    return out

def atr_of(B,p=14):
    n=len(B); tr=[None]*n
    for i in range(1,n):
        h,l,pc=B[i][2],B[i][3],B[i-1][4]; tr[i]=max(h-l,abs(h-pc),abs(l-pc))
    return wilder(tr,p)

def efficiency_ratio(B,W):
    """ER as of END of bar i (known after close of i). Returns list keyed by i."""
    n=len(B); er=[None]*n; c=[b[4] for b in B]
    for i in range(W,n):
        net=abs(c[i]-c[i-W])
        path=sum(abs(c[j]-c[j-1]) for j in range(i-W+1,i+1))
        er[i]=net/path if path>0 else 0.0
    return er

def sweeps(B,k,W):
    """Two-sided liquidity-raid count as of end of bar i.
    swing high at j (fractal k): high[j] > highs within +-k. A raid of that
    high later = a bar pokes above it but CLOSES back below (reverted).
    Count distinct up-raids and down-raids in last W bars. Consolidation
    proxy = min(up_raids, down_raids) >= 1 (both sides hunted)."""
    n=len(B); H=[b[2] for b in B]; L=[b[3] for b in B]; C=[b[4] for b in B]
    sh=[False]*n; sl=[False]*n
    for j in range(k,n-k):
        if all(H[j]>=H[j-d] and H[j]>=H[j+d] for d in range(1,k+1)): sh[j]=True
        if all(L[j]<=L[j-d] and L[j]<=L[j+d] for d in range(1,k+1)): sl[j]=True
    up=[0]*n; dn=[0]*n   # reverted-raid flags per bar
    # precompute recent swing levels available before bar i
    for i in range(k+1,n):
        # nearest prior swing high/low levels (confirmed, i.e. index<=i-k-1)
        hi=None; lo=None
        for j in range(i-k-1, max(-1,i-60), -1):
            if hi is None and sh[j]: hi=H[j]
            if lo is None and sl[j]: lo=L[j]
            if hi is not None and lo is not None: break
        if hi is not None and H[i]>hi and C[i]<hi: up[i]=1   # bull-trap raid of highs
        if lo is not None and L[i]<lo and C[i]>lo: dn[i]=1   # bear-trap raid of lows
    two=[None]*n
    for i in range(W,n):
        u=sum(up[i-W+1:i+1]); d=sum(dn[i-W+1:i+1])
        two[i]=min(u,d)   # >=1 => both-sided liquidity taken => consolidation
    return two

def regime_by_day(unit, er_W, sw_k, sw_W):
    """Return dict: date -> (ER_prevbar, sweep_prevbar) as known at the OPEN of
    that date's session (use the last bar that ENDED on the prior calendar day
    -> no look-ahead into the entry day)."""
    B=resample(load_bars("H1"), unit)
    er=efficiency_ratio(B,er_W); sw=sweeps(B,sw_k,sw_W)
    # map each bar to the date; for entry-day D we want features from last bar
    # whose time.date() < D
    feat={}   # date -> (er, sweep)  using latest fully-closed prior-day bar
    last_by_date={}
    for i,b in enumerate(B):
        last_by_date[b[0].date()]=(er[i],sw[i])
    dates=sorted(last_by_date)
    for idx in range(1,len(dates)):
        e,s=last_by_date[dates[idx-1]]      # prior day's last-bar features
        if e is None or s is None: continue
        feat[dates[idx]]=(e,s)
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

def sharpe_monthly(pairs):
    m=defaultdict(float)
    for t,p in pairs: m[(t.year,t.month)]+=p
    NOM=1_600_000
    v=[m[k]/NOM*100 for k in sorted(m)]
    if len(v)<3: return 0.0
    mu=sum(v)/len(v); sd=math.sqrt(sum((x-mu)**2 for x in v)/(len(v)-1))
    return mu/sd*math.sqrt(12) if sd else 0.0

def evaluate(feat, trades, det, thr):
    """det='er' -> keep trades with ER>=thr (trend). det='sweep' -> keep
    trades with sweep_count < thr (i.e. NOT both-sided-hunted)."""
    kept=[]; skipped=[]
    for t,p in trades:
        f=feat.get(t)
        if not f: kept.append((t,p)); continue   # unknown -> keep (conservative)
        er,sw=f
        if det=="er":
            (kept if er>=thr else skipped).append((t,p))
        else:
            (kept if sw<thr else skipped).append((t,p))
    return kept, skipped

def peryear(pairs):
    y=defaultdict(float)
    for t,p in pairs: y[t.year]+=p
    return y

def main():
    trades=load_trades()
    base_net=sum(p for _,p in trades); base_sh=sharpe_monthly(trades)
    IS=lambda t: t.year<=2021
    is_tr=[(t,p) for t,p in trades if IS(t)]
    oos_tr=[(t,p) for t,p in trades if not IS(t)]
    print(f"BASELINE  net {base_net:>10.0f}  Sharpe {base_sh:.2f}  "
          f"(IS net {sum(p for _,p in is_tr):.0f} / OOS net {sum(p for _,p in oos_tr):.0f})\n")

    configs=[]
    for unit in ("D","H4","H1"):
        for W in ((10,20) if unit=="D" else (24,48)):
            configs.append((unit, "er", W, None, None))
        for (k,swW) in ((2,10),(2,20)) if unit=="D" else ((2,48),(3,96)):
            configs.append((unit, "sweep", None, k, swW))

    for unit,det,erW,swk,swW in configs:
        if det=="er":
            feat=regime_by_day(unit, erW, 2, 20)
            # choose threshold on IS as the 33rd percentile of ER at entry days
            vals=sorted(feat[t][0] for t,_ in is_tr if t in feat)
            thr=vals[int(len(vals)*0.33)] if vals else 0
            tag=f"{unit} ER(W={erW}) keep>={thr:.2f}"
        else:
            feat=regime_by_day(unit, 10, swk, swW)
            thr=1   # skip if both sides raided (sweep_count>=1)
            tag=f"{unit} SWEEP(k={swk},W={swW}) skip if>=1 two-sided"
        # apply on IS then OOS
        def rep(sub):
            kept,skip=evaluate(feat, sub, det, thr)
            return sum(p for _,p in kept), sharpe_monthly(kept), len(skip), sum(p for _,p in skip)
        n_all,s_all,sk_all,skp_all=rep(trades)
        n_is,s_is,_,_=rep(is_tr)
        n_oos,s_oos,_,_=rep(oos_tr)
        y=peryear([(t,p) for t,p in trades])
        ky=peryear(evaluate(feat,trades,det,thr)[0])
        # losing-year improvement
        loss_before=sum(y[yr] for yr in (2018,2020,2026))
        loss_after=sum(ky.get(yr,0) for yr in (2018,2020,2026))
        trend_before=sum(y[yr] for yr in (2022,2024))
        trend_after=sum(ky.get(yr,0) for yr in (2022,2024))
        print(f"{tag:<40}")
        print(f"   ALL   net {n_all:>9.0f} (d{n_all-base_net:>+8.0f}) Sh {s_all:.2f}"
              f"  skipped {sk_all} trades (net {skp_all:+.0f})")
        print(f"   IS  Sh {s_is:.2f}  |  OOS Sh {s_oos:.2f}  (base OOS {sharpe_monthly(oos_tr):.2f})")
        print(f"   loss-yrs {loss_before:+.0f} -> {loss_after:+.0f}   "
              f"trend-yrs {trend_before:+.0f} -> {trend_after:+.0f}"
              f"   ({'GOOD' if loss_after>loss_before and trend_after>0.7*trend_before else 'mixed'})")
        print()

if __name__=="__main__":
    main()
